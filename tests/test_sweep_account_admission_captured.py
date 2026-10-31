"""Captured-program checks for the account admission of the curve fee sweeps.

Every case runs `sweep_protocol_fee` or `sweep_creator_fee` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token and
Associated Token programs. One account set is the expected one from
`tests/test_sweep_fees_captured.py`, on a native or a token quote curve. A case
changes it by one, two or three faults: wrong address, owner, data, mutability
or program.

The same faults go to `programs/pump/recovered/sweep_account_admission_host.rs`,
and the error, the recipient's lamports, the curve's tokens and the event count
must agree. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
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
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_sweep_fees_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/sweep_account_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
STRANGER = Pubkey.from_bytes(bytes([64]) * 32)
FEE_PAYER = Keypair.from_seed(bytes([233]) * 32)
ROUTES = ('protocol_native', 'protocol_token', 'creator_native', 'creator_token')
NAMES = [a['name'] for a in base.IX['sweep_protocol_fee']['accounts']]
TOKEN_STATE = ('key', 'readonly', 'owner', 'short', 'mintdata', 'ownerdata', 'frozen', 'missing')
SLOT_FAULTS = {
    'payer': ('unsigned', 'readonly'),
    'global': ('key', 'owner', 'short', 'disc', 'missing'),
    'base_mint': ('key', 'owner', 'short', 'missing'),
    'quote_mint': ('key', 'other', 'owner', 'short', 'missing'),
    'quote_token_program': ('key', 't22'),
    'associated_token_program': ('key',),
    'system_program': ('key',),
    'bonding_curve': ('key', 'readonly', 'owner', 'short', 'disc', 'missing'),
    'associated_quote_bonding_curve': TOKEN_STATE,
    'recipient': ('readonly', 'other'),
    'associated_quote_recipient': TOKEN_STATE,
    'event_authority': ('key',),
    'program': ('key', 'token'),
}
HOOKS = ('h.empty',)
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'MissingAccount': 'missing_account'}


def faults_of():
    return [f'{slot}.{kind}' for slot in NAMES for kind in SLOT_FAULTS.get(slot, ())] + list(HOOKS)


def rewrite(account, start, value):
    data = bytearray(bytes(account.data))
    data[start:start + len(value)] = value
    return Account(account.lamports, bytes(data), account.owner)


def error_name(result):
    text = str(result.err())
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    if any('panicked' in line for line in result.meta().logs()):
        return 'panic'
    for name, short in RUNTIME.items():
        if name in text:
            return f'error:{short}'
    return f'error:{text}'


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        self.vm.add_program_from_file(base.TOKEN, base.TOKEN_ELF)
        self.vm.add_program_from_file(base.ATA, base.ATA_ELF)
        self.vm.set_clock(base.Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def tokens(self, key):
        account = self.vm.get_account(key)
        return int.from_bytes(bytes(account.data)[64:72], 'little') if account and len(account.data) >= 72 else 0

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        bucket, kind = route.split('_')
        empty = 'h.empty' in faults
        item = base.case(bucket=bucket, native=kind == 'native',
                         **({'creator_fee': 0} if empty and bucket == 'creator' else {}),
                         **({'protocol_fees': 0} if empty and bucket == 'protocol' else {}))
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        mint = base.NATIVE_MINT if kind == 'native' else base.QUOTE_MINT
        recipient = base.VAULT if bucket == 'creator' else base.FEE_RECIPIENT
        curve_ata, recipient_ata = base.ata(base.CURVE, mint), base.ata(recipient, mint)
        keys = {'payer': base.PAYER.pubkey(), 'global': base.GLOBAL, 'base_mint': base.BASE_MINT, 'quote_mint': mint,
                'quote_token_program': base.TOKEN, 'associated_token_program': base.ATA, 'system_program': base.SYSTEM,
                'bonding_curve': base.CURVE, 'associated_quote_bonding_curve': curve_ata, 'recipient': recipient,
                'associated_quote_recipient': recipient_ata, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        accounts = {
            base.PAYER.pubkey(): Account(10**12, b'', base.SYSTEM),
            base.GLOBAL: Account(10**9, base.global_data(), base.PUMP),
            base.BASE_MINT: Account(10**9, base.mint_data(), base.TOKEN),
            base.NATIVE_MINT: Account(10**9, base.mint_data(9), base.TOKEN),
            base.QUOTE_MINT: Account(10**9, base.mint_data(), base.TOKEN),
            base.OTHER: Account(10**9, base.mint_data(), base.TOKEN),
            base.CURVE: Account(base.curve_lamports(item), base.curve_data(item), base.PUMP),
            recipient: Account(10**9, b'', base.SYSTEM),
            curve_ata: Account(base.TOKEN_RENT, base.token_data(mint, base.CURVE, 10**10), base.TOKEN),
            recipient_ata: Account(base.TOKEN_RENT, base.token_data(mint, recipient, 0), base.TOKEN),
        }
        read_only, unsigned = set(), False
        for fault in faults:
            slot, name = fault.split('.')
            if slot == 'h':
                continue
            key = keys[slot]
            present = accounts.get(key)
            if name == 'readonly':
                read_only.add(slot)
            elif name == 'unsigned':
                unsigned = True
            elif name == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES.index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif name == 'other' and slot == 'quote_mint':
                keys[slot] = base.OTHER
            elif name == 'other':
                # A stranger with its own quote token account, so seeds pass.
                old = keys['associated_quote_recipient']
                keys[slot] = STRANGER
                keys['associated_quote_recipient'] = base.ata(STRANGER, mint)
                accounts[STRANGER] = accounts.pop(key)
                accounts[keys['associated_quote_recipient']] = Account(
                    base.TOKEN_RENT, base.token_data(mint, STRANGER, 0), base.TOKEN)
                accounts.pop(old, None)
            elif name == 'token':
                keys[slot] = base.TOKEN
            elif name == 't22':
                keys[slot] = TOKEN22
            elif name == 'missing':
                accounts.pop(key, None)
            elif present is None:
                continue
            elif name == 'owner':
                accounts[key] = Account(present.lamports, bytes(present.data), ALIEN)
            elif name == 'short':
                accounts[key] = Account(present.lamports, bytes(4), present.owner)
            elif name == 'disc':
                accounts[key] = rewrite(present, 0, bytes(8))
            elif len(present.data) == 165:
                value = {'mintdata': (0, bytes([9]) * 32), 'ownerdata': (32, bytes([9]) * 32), 'frozen': (108, b'\x02')}
                accounts[key] = rewrite(present, *value[name])
        for key, account in accounts.items():
            self.put(key, account)
        ix = base.IX['sweep_creator_fee' if bucket == 'creator' else 'sweep_protocol_fee']
        metas = [AccountMeta(keys[a['name']], a.get('signer', False) and not unsigned,
                             a.get('writable', False) and a['name'] not in read_only) for a in ix['accounts']]
        signers = [FEE_PAYER] if unsigned else [FEE_PAYER, base.PAYER]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(ix['discriminator']), metas)],
                                               FEE_PAYER.pubkey(), signers, self.vm.latest_blockhash())
        source = keys['associated_quote_bonding_curve']
        before = self.lamports(keys['recipient']), self.tokens(source)
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        return f"ok,{self.lamports(keys['recipient']) - before[0]},{before[1] - self.tokens(source)},{events}"


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1600, seed=1443):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(ROUTES, k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class SweepAccountAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'sweep-account-admission-host'
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
        for changed in ('error:2000', 'ok,1,0,1'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([('protocol_native', ())])
        self.assertEqual(answers([('protocol_native', ())]), [self.harness.run('protocol_native', ())])

    def test_stored_recipient_token_authority_is_never_read(self):
        for route in ('protocol_token', 'creator_token'):
            faults = ('associated_quote_recipient.ownerdata',)
            self.assertEqual(self.harness.run(route, faults), self.harness.run(route, ()))

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3001, 3002, 3007, 3008, 3010, 3012, 4, 17, 6000, 6004, 6010)}
                         | {'error:invalid_account_data', 'error:missing_account'})
        self.assertLessEqual({'ok,7000000,0,1', 'ok,0,7000000,1', 'ok,3000000,0,1', 'ok,0,3000000,1', 'ok,0,0,0'}, answers)


if __name__ == '__main__':
    unittest.main()
