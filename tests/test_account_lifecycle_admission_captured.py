"""Captured-program checks for the account admission of the three lifecycle instructions.

Every case runs `init_user_volume_accumulator`, `close_user_volume_accumulator` or
`extend_account` from the captured `evidence/original/pump/deployed.so` on LiteSVM.
One account set is the expected one from `tests/test_account_lifecycle_captured.py`.
A case changes it by one, two or three faults: wrong address, owner, data,
mutability, signature or program.

The same faults go to `programs/pump/recovered/account_lifecycle_admission_host.rs`,
and the error, or the event count and the subject's lamports and length, must agree.
This shows matching behavior on these inputs only; it is not a byte-identity claim.
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
import test_account_lifecycle_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/account_lifecycle_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([68]) * 32)
FEE_PAYER = Keypair.from_seed(bytes([243]) * 32)
ROUTES = ('create', 'init', 'close', 'extend')
INSTRUCTIONS = {'create': 'init_user_volume_accumulator', 'init': 'init_user_volume_accumulator',
                'close': 'close_user_volume_accumulator', 'extend': 'extend_account'}
NAMES = {route: [a['name'] for a in base.IX[name]['accounts']] for route, name in INSTRUCTIONS.items()}
TAIL = {'system_program': ('key',), 'event_authority': ('key',), 'program': ('key', 'system')}
SLOT_FAULTS = {
    'create': {'payer': ('unsigned', 'readonly', 'poor'), 'user': ('key',),
               'user_volume_accumulator': ('key', 'readonly', 'owner', 'sysdata', 'funded'), **TAIL},
    'init': {'payer': ('unsigned', 'readonly'), 'user': ('key',),
             'user_volume_accumulator': ('key', 'readonly', 'owner', 'short', 'disc', 'trunc', 'long', 'poorrent'), **TAIL},
    'close': {'user': ('unsigned', 'readonly'),
              'user_volume_accumulator': ('key', 'readonly', 'owner', 'short', 'disc', 'trunc', 'missing'), **TAIL},
    'extend': {'account': ('readonly', 'owner', 'missing', 'unknown', 'short', 'poorrent'),
               'user': ('unsigned', 'readonly', 'poor'), **TAIL},
}
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'MissingAccount': 'missing_account',
           'PrivilegeEscalation': 'privilege_escalation', 'InsufficientFundsForRent': 'rent',
           'ReadonlyLamportChange': 'readonly_lamports', 'ReadonlyDataModified': 'readonly_data',
           'ExternalAccountDataModified': 'external_data_modified', 'AccountDataSizeChanged': 'size_changed',
           'ExternalAccountLamportSpend': 'external_lamport_spend'}


def faults_of(route):
    return [f'{slot}.{kind}' for slot in NAMES[route] for kind in SLOT_FAULTS[route].get(slot, ())]


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
        self.vm.set_clock(Clock(100, base.NOW, 0, 0, base.NOW))
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
        ix = base.IX[INSTRUCTIONS[route]]
        keys = {'payer': base.PAYER.pubkey(), 'user': base.USER.pubkey(), 'user_volume_accumulator': base.UVA,
                'account': base.TARGET, 'system_program': base.SYSTEM, 'event_authority': base.EVENT_AUTHORITY,
                'program': base.PUMP}
        accounts = {base.PAYER.pubkey(): Account(10**12, b'', base.SYSTEM),
                    base.USER.pubkey(): Account(10**9, b'', base.SYSTEM)}
        if route in ('init', 'close'):
            accounts[base.UVA] = Account(base.UVA_RENT, base.uva_body(base.case('close')), base.PUMP)
        if route == 'extend':
            accounts[base.TARGET] = Account(10**9, base.KIND_DISC['bc'] + bytes(73), base.PUMP)
        read_only, unsigned = set(), set()
        for fault in faults:
            slot, kind = fault.split('.')
            key = keys[slot]
            present = accounts.get(key)
            if kind == 'readonly':
                read_only.add(slot)
            elif kind == 'unsigned':
                unsigned.add(slot)
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES[route].index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif kind == 'system':
                keys[slot] = base.SYSTEM
            elif kind == 'missing':
                accounts.pop(key, None)
            elif kind == 'poor':
                accounts[key] = Account(1000, b'', base.SYSTEM)
            elif kind == 'funded':
                accounts[key] = Account(10**7, b'', base.SYSTEM)
            elif kind == 'sysdata':
                accounts[key] = Account(10**9, bytes(137), base.SYSTEM)
            elif kind == 'owner' and present is None:
                accounts[key] = Account(10**9, b'', ALIEN)
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
            elif kind == 'unknown':
                accounts[key] = rewrite(present, 0, base.KIND_DISC['junk'])
            elif kind == 'long':
                accounts[key] = Account(10**9, bytes(present.data).ljust(138, b'\0'), present.owner)
            elif kind == 'poorrent':
                accounts[key] = Account(1, bytes(present.data), present.owner)
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], a.get('signer', False) and a['name'] not in unsigned,
                             a.get('writable', False) and a['name'] not in read_only) for a in ix['accounts']]
        signers = [FEE_PAYER] + [k for name, k in (('payer', base.PAYER), ('user', base.USER))
                                 if any(m.is_signer and m.pubkey == k.pubkey() for m in metas)]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(ix['discriminator']), metas)],
                                               FEE_PAYER.pubkey(), signers, self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        subject = self.vm.get_account(keys['account' if route == 'extend' else 'user_volume_accumulator'])
        lamports, length = (subject.lamports, len(subject.data)) if subject else (0, 0)
        return f'ok,{events},{lamports},{length}'


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of(route)] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(route), 2)]


def triple_cases(count=1000, seed=4195):
    rng = random.Random(seed)
    cases = []
    for route in rng.choices(ROUTES, k=count):
        faults = faults_of(route)
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class AccountLifecycleAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'account-lifecycle-admission-host'
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
        for changed in ('error:2000', 'ok,0,0,0'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([('close', ())])
        self.assertEqual(answers([('close', ())]), [self.harness.run('close', ())])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (0, 1, 2000, 2004, 2005, 2006, 2019, 3001, 3002, 3003, 3007, 3008, 3010,
                                                 3012, 6010)}
                         | {'error:privilege_escalation', 'error:missing_account', 'error:rent'})
        self.assertLessEqual({'ok,1,1844400,137', 'ok,1,10000000,137', 'ok,1,0,0', 'ok,1,1000591600,166'}, answers)


if __name__ == '__main__':
    unittest.main()
