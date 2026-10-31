"""Captured-program checks for the account admission of `sync_user_volume_accumulator`.

Every case runs `sync_user_volume_accumulator` from the captured
`evidence/original/pump/deployed.so` on LiteSVM. One account set is the expected
one from `tests/test_token_incentives_captured.py`, on a call that resets the
claimed tokens or on one that changes nothing. A case changes it by one, two or
three faults: wrong address, owner, data, mutability or program.

The same faults go to `programs/pump/recovered/volume_sync_admission_host.rs`, and
the error, or the event count and the stored total, must agree. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_token_incentives_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = {base.PUMP_ELF: base.ELF_SHA256[base.PUMP_ELF]}
HOST_SOURCE = ROOT / 'programs/pump/recovered/volume_sync_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
ROUTES = ('reset', 'idle')
IX = base.IX['sync_user_volume_accumulator']
NAMES = [a['name'] for a in IX['accounts']]
SLOT_FAULTS = {
    'user': ('key',),
    'global_volume_accumulator': ('key', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'user_volume_accumulator': ('key', 'readonly', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'event_authority': ('key',),
    'program': ('key', 'token'),
}
CASES = {'reset': dict(op='sync', now=base.START - 1, last_update=base.START - 10, claimed=50, has_claimed=True),
         'idle': dict(op='sync', claimed=50, has_claimed=True)}
RUNTIME = {'MissingAccount': 'missing_account'}


def faults_of():
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
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        item = base.case(**CASES[route])
        self.vm.set_clock(base.Clock(100, item['now'], 0, 0, item['now']))
        self.put(base.PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        keys = {'user': base.USER, 'global_volume_accumulator': base.GLOBAL_VOLUME,
                'user_volume_accumulator': base.USER_VOLUME, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        accounts = {
            base.GLOBAL_VOLUME: Account(10**9, base.global_volume_data(item), base.PUMP),
            base.USER_VOLUME: Account(10**9, base.user_volume_data(item), base.PUMP),
        }
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
            elif kind == 'token':
                keys[slot] = base.TOKEN
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
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], False, a.get('writable', False) and a['name'] not in read_only) for a in IX['accounts']]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(IX['discriminator']), metas)],
                                               base.PAYER.pubkey(), [base.PAYER], self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        stored = struct.unpack_from('<Q', bytes(self.vm.get_account(keys['user_volume_accumulator']).data), 49)[0]
        return f'ok,{events},{stored}'


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1000, seed=1850):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(ROUTES, k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class VolumeSyncAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'volume-sync-admission-host'
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
                    self.run_cases([('reset', ())])
        self.assertEqual(answers([('reset', ())]), [self.harness.run('reset', ())])

    def test_unchecked_program_slot_passes_without_an_event(self):
        for fault in ('program.key', 'program.token'):
            self.assertEqual(self.harness.run('reset', (fault,)), 'error:missing_account')
            self.assertEqual(self.harness.run('idle', (fault,)), 'ok,0,50')

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3001, 3002, 3003, 3007, 3012)} | {'error:missing_account'})
        self.assertLessEqual({'ok,1,0', 'ok,0,50'}, answers)


if __name__ == '__main__':
    unittest.main()
