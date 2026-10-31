"""Captured-program checks for the account admission of `initialize_quote_control`.

Every case runs `initialize_quote_control` from the captured
`evidence/original/pump/deployed.so` on LiteSVM. A case changes the plain call by
up to four faults: a wrong, dropped, read-only or unsigned account, or what the
payer and the `quote-control` address already hold.

The same faults go to `programs/pump/recovered/quote_control_init_host.rs`. The
error, or the payment, the lamports and every stored byte, must agree. Signature
checks are off, so a case can mark the PDA as a signer. This shows matching
behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
import random
import re
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_quote_control_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/quote_control_init_host.rs'

ALIEN = Pubkey.from_bytes(bytes([70]) * 32)
WRONG_CONTROL = Pubkey.from_bytes(bytes([121]) * 32)
WRONG_SYSTEM = Pubkey.from_bytes(bytes([122]) * 32)
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
FEE_PAYER = Keypair.from_seed(bytes([244]) * 32)
USER = Keypair.from_seed(bytes([245]) * 32)
LENGTH = 2108
RENT = base.rent(LENGTH)
SMALL = 1000
SYSTEM = base.SYSTEM
PUMP = base.PUMP
CONTROL_SHAPES = {'funded': (RENT, 0, SYSTEM), 'richer': (RENT + 1, 0, SYSTEM), 'one_short': (RENT - 1, 0, SYSTEM),
                  'partial': (SMALL, 0, SYSTEM),
                  'spaced': (RENT, 10, SYSTEM), 'spaced_partial': (SMALL, 10, SYSTEM), 'pump': (RENT, LENGTH, PUMP),
                  'foreign': (RENT, LENGTH, ALIEN), 'foreign_empty': (RENT, 0, ALIEN),
                  'foreign_partial': (SMALL, 0, ALIEN)}
USER_SHAPES = {'absent': (0, 0, SYSTEM), 'poor': (SMALL, 0, SYSTEM), 'exact': (RENT, 0, SYSTEM),
               'exact_partial': (RENT - SMALL, 0, SYSTEM), 'dust': (RENT + SMALL, 0, SYSTEM),
               'data': (10**10, 10, SYSTEM), 'poor_data': (SMALL, 10, SYSTEM), 'foreign': (10**10, 0, ALIEN),
               'foreign_poor': (SMALL, 0, ALIEN), 'foreign_data': (10**10, 10, ALIEN)}
SLOT_FAULTS = {
    'quote_control': ('key', 'readonly', 'signed', *CONTROL_SHAPES, 'dropped'),
    'user': ('unsigned', 'readonly', *USER_SHAPES, 'self', 'dropped'),
    'system_program': ('key', 'token', 'dropped'),
    'h': ('trailing', 'extra'),
}
RUNTIME = {'PrivilegeEscalation': 'privilege_escalation', 'InvalidArgument': 'invalid_argument',
           'ExternalAccountLamportSpend': 'external_lamport_spend'}


def faults_of():
    return [f'{slot}.{kind}' for slot, kinds in SLOT_FAULTS.items() for kind in kinds]


def error_name(result):
    text = str(result.err())
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name, short in RUNTIME.items():
        if name in text:
            return f'error:{short}'
    return f'error:{text}'


def stored_shape(lamports, length, owner):
    return Account(lamports, bytes(length), owner)


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, base.PUMP_ELF)
        self.vm.set_clock(Clock(100, base.NOW, 0, 0, base.NOW))

    def run(self, faults):
        for key in (base.QUOTE_CONTROL, WRONG_CONTROL, USER.pubkey()):
            self.vm.set_account(key, Account(0, b'', SYSTEM))
        self.vm.expire_blockhash()
        keys = {'quote_control': base.QUOTE_CONTROL, 'user': USER.pubkey(), 'system_program': SYSTEM}
        user_shape, control_shape = (10**10, 0, SYSTEM), None
        read_only, dropped, signed = set(), set(), {'user'}
        data = bytes(base.IX['init']['discriminator'])
        extra = False
        for fault in faults:
            slot, kind = fault.split('.')
            if kind == 'readonly':
                read_only.add(slot)
            elif kind == 'dropped':
                dropped.add(slot)
            elif kind == 'signed':
                signed.add(slot)
            elif kind == 'unsigned':
                signed.discard(slot)
            elif fault == 'quote_control.key':
                keys[slot] = WRONG_CONTROL
            elif fault == 'system_program.key':
                keys[slot] = WRONG_SYSTEM
            elif kind == 'token':
                keys[slot] = TOKEN
            elif kind == 'self':
                keys[slot] = keys['quote_control']
            elif kind == 'trailing':
                data += b'\x07'
            elif kind == 'extra':
                extra = True
            elif slot == 'user':
                user_shape = USER_SHAPES[kind]
            else:
                control_shape = CONTROL_SHAPES[kind]
        self.vm.set_account(FEE_PAYER.pubkey(), Account(10**12, b'', SYSTEM))
        self.vm.set_account(USER.pubkey(), stored_shape(*user_shape))
        if control_shape:
            self.vm.set_account(base.QUOTE_CONTROL, stored_shape(*control_shape))
        metas = [AccountMeta(keys[a['name']], a['name'] in signed,
                             a.get('writable', False) and a['name'] not in read_only)
                 for a in base.IX['init']['accounts'] if a['name'] not in dropped]
        if extra:
            metas.append(AccountMeta(ALIEN, False, False))
        blockhash = self.vm.latest_blockhash()
        tx = Transaction.new_unsigned(Message.new_with_blockhash([Instruction(PUMP, data, metas)],
                                                                 FEE_PAYER.pubkey(), blockhash))
        tx.partial_sign([FEE_PAYER], blockhash)
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        stored = self.vm.get_account(base.QUOTE_CONTROL)
        after = self.vm.get_account(USER.pubkey())
        return ('ok', user_shape[0] - (after.lamports if after else 0), stored.lamports, str(stored.owner), bytes(stored.data),
                sum(1 for line in result.logs() if line.startswith('Program data: ')))


def single_cases():
    return [()] + [(fault,) for fault in faults_of()]


def pair_cases():
    return list(itertools.combinations(faults_of(), 2))


def triple_cases():
    return list(itertools.combinations(faults_of(), 3))


def four_fault_cases(count=2000, seed=7361):
    rng = random.Random(seed)
    faults = faults_of()
    # In the list's order, as the pairs are: a slot's later fault wins.
    return [tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 4))) for _ in range(count)]


def host_line(faults):
    return ' '.join(faults) or '-'


class QuoteControlInitCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in base.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'quote-control-init-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.harness = Harness()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(case) + '\n' for case in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def mismatch(self, answer, captured):
        if answer.startswith('error:'):
            return answer != captured
        if isinstance(captured, str):
            return True
        _, paid, lamports = answer.split(',')
        expected = base.serialize(0, 0, ())
        return captured != ('ok', int(paid), int(lamports), str(PUMP), expected + bytes(LENGTH - len(expected)), 0)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        bad = []
        for case, answer in zip(cases, answers):
            captured = self.harness.run(case)
            if self.mismatch(answer, captured):
                bad.append((case, answer, captured if isinstance(captured, str) else captured[:4]))
        self.assertEqual(bad[:5], [], len(bad))

    def test_single_faults_match_captured_program(self):
        self.run_cases(single_cases())

    def test_fault_pairs_match_captured_program(self):
        self.run_cases(pair_cases())

    def test_fault_triples_match_captured_program(self):
        self.run_cases(triple_cases())

    def test_four_fault_cases_match_captured_program(self):
        self.run_cases(four_fault_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: a passing run must fail once the payment, the
        # lamports, the error or a stored byte changes.
        for case, answer in zip(((), ('quote_control.partial',)), self.host_answers([(), ('quote_control.partial',)])):
            captured = self.harness.run(case)
            self.assertFalse(self.mismatch(answer, captured))
            self.assertTrue(self.mismatch('error:0', captured))
            word, paid, lamports = answer.split(',')
            self.assertTrue(self.mismatch(f'{word},{int(paid) + 1},{lamports}', captured))
            self.assertTrue(self.mismatch(f'{word},{paid},{int(lamports) + 1}', captured))
            flipped = bytearray(captured[4])
            flipped[LENGTH - 1] ^= 1
            self.assertTrue(self.mismatch(answer, captured[:4] + (bytes(flipped),) + captured[5:]))
        self.assertFalse(self.mismatch('error:3008', self.harness.run(('system_program.key',))))
        self.assertTrue(self.mismatch('error:3010', self.harness.run(('system_program.key',))))

    def test_cases_cover_every_stop(self):
        answers = self.host_answers(single_cases() + pair_cases())
        self.assertEqual({a for a in answers if a.startswith('error:')}, {
            'error:0', 'error:1', 'error:2000', 'error:2006', 'error:3005', 'error:3008', 'error:3010', 'error:4101',
            'error:privilege_escalation', 'error:invalid_argument', 'error:external_lamport_spend'})
        self.assertIn(f'ok,{RENT},{RENT}', answers)
        self.assertIn(f'ok,0,{RENT}', answers)
        self.assertIn(f'ok,0,{RENT + 1}', answers)
        self.assertIn(f'ok,{RENT - SMALL},{RENT}', answers)


if __name__ == '__main__':
    unittest.main()
