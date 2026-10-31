"""Captured-program checks for the account admission of `claim_cashback`.

Every case runs `claim_cashback` from the captured `evidence/original/pump/deployed.so`
on LiteSVM. One account set is the expected one from
`tests/test_claim_cashback_captured.py`, on an accumulator that holds a claim or
one that holds none. A case changes it by one, two or three faults: wrong address,
owner, data, mutability or program.

The same faults go to `programs/pump/recovered/claim_cashback_admission_host.rs`, and
the error, or the event count and the lamports the user received, must agree. This
shows matching behavior on these inputs only; it is not a byte-identity claim.
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
import test_claim_cashback_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/claim_cashback_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([69]) * 32)
FEE_PAYER = Keypair.from_seed(bytes([244]) * 32)
ROUTES = ('claim', 'empty')
NAMES = [a['name'] for a in base.IX['accounts']]
SLOT_FAULTS = {
    'user': ('key', 'readonly', 'missing'),
    'user_volume_accumulator': ('key', 'readonly', 'owner', 'short', 'disc', 'trunc', 'badbool', 'missing'),
    'system_program': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'system'),
}
EXTRA = {'claim': 1_000_000, 'empty': 0}
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'MissingAccount': 'missing_account',
           'PrivilegeEscalation': 'privilege_escalation', 'InsufficientFundsForRent': 'rent',
           'ReadonlyLamportChange': 'readonly_lamports', 'ReadonlyDataModified': 'readonly_data',
           'ExternalAccountDataModified': 'external_data_modified', 'AccountDataSizeChanged': 'size_changed',
           'ExternalAccountLamportSpend': 'external_lamport_spend'}


def faults_of(route='claim'):
    return [f'{slot}.{kind}' for slot in NAMES for kind in SLOT_FAULTS[slot]]


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
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        item = base.case(extra=EXTRA[route])
        uva = base.uva_key(base.USER)
        keys = {'user': base.USER, 'user_volume_accumulator': uva, 'system_program': base.SYSTEM,
                'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        accounts = {base.USER: Account(10**9, b'', base.SYSTEM), uva: Account(item['lamports'], base.uva_data(item), base.PUMP)}
        read_only = set()
        for fault in faults:
            slot, kind = fault.split('.')
            key = keys[slot]
            present = accounts.get(key)
            if kind == 'readonly':
                read_only.add(slot)
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES.index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif kind == 'system':
                keys[slot] = base.SYSTEM
            elif kind == 'missing':
                accounts.pop(key, None)
            elif present is None:
                continue
            elif kind == 'owner':
                accounts[key] = Account(present.lamports, bytes(present.data), ALIEN)
            elif kind == 'short':
                accounts[key] = Account(present.lamports, bytes(4), present.owner)
            elif kind == 'trunc':
                accounts[key] = Account(present.lamports, bytes(present.data)[:8], present.owner)
            elif kind == 'disc':
                accounts[key] = rewrite(present, 0, bytes(8))
            elif kind == 'badbool':
                accounts[key] = rewrite(present, 40, b'\x02')
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], False, a.get('writable', False) and a['name'] not in read_only)
                 for a in base.IX['accounts']]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(base.IX['discriminator']), metas)],
                                               FEE_PAYER.pubkey(), [FEE_PAYER], self.vm.latest_blockhash())
        before = self.lamports(keys['user'])
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        return f"ok,{events},{self.lamports(keys['user']) - before}"

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of(route)] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(route), 2)]


def triple_cases(count=800, seed=4196):
    rng = random.Random(seed)
    cases = []
    for route in rng.choices(ROUTES, k=count):
        faults = faults_of(route)
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class ClaimCashbackAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'claim-cashback-admission-host'
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
        for changed in ('error:2000', 'ok,0,0'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([('claim', ())])
        self.assertEqual(answers([('claim', ())]), [self.harness.run('claim', ())])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3001, 3002, 3003, 3007, 3008, 3012)})
        self.assertLessEqual({'ok,1,1000000', 'ok,0,0'}, answers)


if __name__ == '__main__':
    unittest.main()
