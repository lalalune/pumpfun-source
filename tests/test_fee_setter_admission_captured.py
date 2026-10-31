"""Captured-program checks for the account admission of `set_params` and `set_reserved_fee_recipients`.

Every case runs one of the two setters from the captured
`evidence/original/pump/deployed.so` on LiteSVM, on the `Global` account and the
eight recipients of `tests/test_fee_params_captured.py`. A case changes that call by
one, two or three faults: wrong address, owner, data, mutability, signature, a dropped
account, a bad recipient or bad arguments.

The same faults go to `programs/pump/recovered/fee_setter_admission_host.rs`, and the
error, or the event count and the changed bytes of `Global`, must agree. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
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
from unittest import mock

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_fee_params_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/fee_setter_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([70]) * 32)
OTHER_AUTHORITY = Pubkey.from_bytes(bytes([71]) * 32)
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
FEE_PAYER = Keypair.from_seed(bytes([244]) * 32)
ROUTES = ('set_params', 'set_reserved_fee_recipients')
SLOT_FAULTS = {
    'global': ('key', 'owner', 'short', 'disc', 'trunc', 'missing', 'readonly', 'stored'),
    'authority': ('unsigned', 'readonly'),
    'event_authority': ('key', 'dropped'),
    'program': ('key', 'token', 'dropped'),
}
HOOKS = ('h.args', 'h.seven', 'h.zero', 'h.poor', 'h.unsorted', 'h.program', 'h.supply')
RUNTIME = {'MissingAccount': 'missing_account', 'NotEnoughAccountKeys': 'not_enough_keys'}


def faults_of():
    return [f'{slot}.{kind}' for slot, kinds in SLOT_FAULTS.items() for kind in kinds] + list(HOOKS)


def error_name(result):
    text = str(result.err())
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name, short in RUNTIME.items():
        if name in text:
            return f'error:{short}'
    return f'error:{text}'


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        self.vm.set_clock(Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        ix = base.IX[route]
        recipients = list(base.SORTED)
        changes = {}
        keys = {'global': base.GLOBAL, 'authority': base.AUTHORITY.pubkey(), 'event_authority': base.EVENT_AUTHORITY,
                'program': base.PUMP}
        data = base.old_global()
        owner = base.PUMP
        present = True
        read_only, dropped, unsigned = set(), set(), False
        cut_args = False
        for fault in faults:
            slot, kind = fault.split('.')
            if fault == 'h.args':
                cut_args = True
            elif fault == 'h.seven':
                recipients = recipients[:7]
            elif fault == 'h.zero':
                recipients[6] = base.recipient(0)
            elif fault == 'h.poor':
                recipients[5] = base.recipient(150, 1)
            elif fault == 'h.unsorted':
                recipients[3], recipients[4] = recipients[4], recipients[3]
            elif fault == 'h.program':
                recipients[2] = base.recipient(base.EXECUTABLE)
            elif fault == 'h.supply':
                changes['supply'] = 1
            elif kind == 'readonly':
                read_only.add(slot)
            elif kind == 'unsigned':
                unsigned = True
            elif kind == 'dropped':
                dropped.add(slot)
            elif kind == 'token':
                keys[slot] = TOKEN
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([200 + list(SLOT_FAULTS).index(slot)]) * 32)
            elif kind == 'owner':
                owner = ALIEN
            elif kind == 'short':
                data = data[:4]
            elif kind == 'trunc':
                data = data[:8]
            elif kind == 'disc':
                data = bytes(8) + data[8:]
            elif kind == 'missing':
                present = False
            elif kind == 'stored' and len(data) >= 41:
                data = data[:9] + bytes(OTHER_AUTHORITY) + data[41:]
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        self.put(base.AUTHORITY.pubkey(), Account(10**10, b'', base.SYSTEM))
        if present:
            self.put(keys['global'], Account(10**9, data, owner))
        for fill, lamports, size in recipients:
            if fill and fill != base.EXECUTABLE:
                self.put(base.key(fill), Account(lamports, bytes(size), base.SYSTEM))
        item = (base.params if route == 'set_params' else base.reserved)(**({} if route != 'set_params' else changes))
        args = base.ix_data(item)
        if cut_args:
            args = args[:-1]
        metas = []
        for a in ix['accounts']:
            if a['name'] in dropped:
                continue
            metas.append(AccountMeta(keys[a['name']], a.get('signer', False) and not unsigned,
                                     a.get('writable', False) and a['name'] not in read_only))
        if not dropped:
            metas += [AccountMeta(base.key(fill), False, False) for fill, *_ in recipients]
        signers = [FEE_PAYER] if unsigned else [FEE_PAYER, base.AUTHORITY]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, args, metas)], FEE_PAYER.pubkey(), signers,
                                               self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        after = bytes(self.vm.get_account(keys['global']).data)
        changed = [i for i in range(len(after)) if i >= len(data) or after[i] != data[i]]
        return f'ok,{events},{changed[0]},{changed[-1]}' if changed else f'ok,{events},-,-'


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1500, seed=4196):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(ROUTES, k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class FeeSetterAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest = hashlib.sha256(base.PUMP_ELF.read_bytes()).hexdigest()
        assert digest == ELF_SHA256, digest
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'fee-setter-admission-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.harness = Harness()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(*case) + '\n' for case in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        wrong = []
        for case, answer in zip(cases, answers):
            captured = self.harness.run(*case)
            if captured != answer:
                wrong.append((case, answer, captured))
        self.assertEqual(wrong[:40], [], f'{len(wrong)} of {len(cases)} differ')

    def test_single_faults_match_captured_program(self):
        self.run_cases(single_cases())

    def test_fault_pairs_match_captured_program(self):
        self.run_cases(pair_cases())

    def test_seeded_triples_match_captured_program(self):
        self.run_cases(triple_cases())

    def test_checker_rejects_a_changed_answer(self):
        # Negative control: run_cases must fail when the host's answer changes.
        answers = self.host_answers
        case = ('set_params', ())
        for changed in ('error:2000', 'ok,0,-,-'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([case])
        self.assertEqual(answers([case]), [self.harness.run(*case)])


    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (102, 2000, 2005, 2006, 2007, 3001, 3002, 3003, 3005, 3007, 3010, 3012,
                                                 6000, 6011, 6027, 6028, 6029)}
                         | {'error:missing_account'})
        self.assertLessEqual({'ok,1,41,449', 'ok,1,451,739'}, answers)


if __name__ == '__main__':
    unittest.main()
