"""Captured-program checks for the account admission of the Pump global setters.

Every case runs one of eleven setters from the captured
`evidence/original/pump/deployed.so` on LiteSVM, on the `Global` account of
`tests/test_global_admin_captured.py`. One call per setter is the expected one. A
case changes it by one, two or three faults: wrong address, owner, data, mutability,
signature, a dropped account, or bad arguments.

The same faults go to `programs/pump/recovered/admin_setter_admission_host.rs`, and
the error, or the event count and the changed bytes of `Global`, must agree. This
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
import test_global_admin_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOST_SOURCE = ROOT / 'programs/pump/recovered/admin_setter_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([68]) * 32)
OTHER_AUTHORITY = Pubkey.from_bytes(bytes([69]) * 32)
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
FEE_PAYER = Keypair.from_seed(bytes([243]) * 32)
ROUTES = {
    'add_quote_mint': bytes(base.USDC),
    'remove_quote_mint': bytes(base.USDC),
    'update_buyback_config': b'\x01' + (42).to_bytes(8, 'little'),
    'set_max_curve_depth': bytes([3]),
    'set_virtual_quote_reserves': (5).to_bytes(8, 'little'),
    'update_creator_fee_config': bytes([1]) + (5000).to_bytes(8, 'little'),
    'update_holder_reward_config': bytes([1]) + bytes(base.OTHER),
    'toggle_create_v2': bytes([1]),
    'toggle_mayhem_mode': bytes([1]),
    'toggle_cashback_enabled': bytes([1]),
    'update_global_authority': b'',
}
SLOT_FAULTS = {
    'global': ('key', 'owner', 'short', 'disc', 'trunc', 'missing', 'readonly', 'stored'),
    'authority': ('unsigned', 'readonly'),
    'event_authority': ('key', 'dropped'),
    'program': ('key', 'token', 'dropped'),
}
HOOKS = ('h.emptyarg',)
RUNTIME = {'MissingAccount': 'missing_account', 'NotEnoughAccountKeys': 'not_enough_keys'}


def faults_of():
    return [f'{slot}.{kind}' for slot, kinds in SLOT_FAULTS.items() for kind in kinds] + list(HOOKS)


def ix_of(route):
    return next(i for i in base.IDL['instructions'] if i['name'] == route)


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
        self.vm.add_program_from_file(base.PROGRAM, base.ELF)
        self.vm.set_clock(Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.Pubkey.default()))
        self.stale.clear()
        self.vm.expire_blockhash()
        ix = ix_of(route)
        before = base.global_data(whitelist=base.USDC if route == 'remove_quote_mint' else None, bps=7)
        keys = {'global': base.GLOBAL, 'authority': base.AUTH.pubkey(), 'new_authority': base.OTHER,
                'event_authority': base.EVENT, 'program': base.PROGRAM}
        data = before
        owner = base.PROGRAM
        present = True
        read_only, dropped, unsigned = set(), set(), False
        arg = ROUTES[route]
        for fault in faults:
            slot, kind = fault.split('.')
            if fault == 'h.emptyarg':
                arg = arg[:-1]
            elif kind == 'readonly':
                read_only.add(slot)
            elif kind == 'unsigned':
                unsigned = True
            elif kind == 'dropped':
                dropped.add(slot)
            elif kind == 'token':
                keys[slot] = TOKEN
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([110 + list(SLOT_FAULTS).index(slot)]) * 32)
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
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.Pubkey.default()))
        self.put(base.AUTH.pubkey(), Account(10**10, b'', base.Pubkey.default()))
        if present:
            self.put(keys['global'], Account(10**9, data, owner))
        metas = []
        for a in ix['accounts']:
            if a['name'] in dropped:
                continue
            metas.append(AccountMeta(keys[a['name']], a.get('signer', False) and not unsigned,
                                     a.get('writable', False) and a['name'] not in read_only))
        signers = [FEE_PAYER] if unsigned else [FEE_PAYER, base.AUTH]
        tx = Transaction.new_signed_with_payer([Instruction(base.PROGRAM, bytes(ix['discriminator']) + arg, metas)],
                                               FEE_PAYER.pubkey(), signers, self.vm.latest_blockhash())
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


def triple_cases(count=1500, seed=4195):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(list(ROUTES), k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class AdminSetterAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        digest = hashlib.sha256(base.ELF.read_bytes()).hexdigest()
        assert digest == base.ELF_SHA256, digest
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'admin-setter-admission-host'
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
        case = ('toggle_create_v2', ())
        for changed in ('error:2000', 'ok,0,-,-'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([case])
        self.assertEqual(answers([case]), [self.harness.run(*case)])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (102, 2000, 2006, 3001, 3002, 3003, 3005, 3007, 3010, 3012, 6000)}
                         | {'error:missing_account'})
        self.assertEqual(sum(a.startswith('ok,1,') for a in self.host_answers([(r, ()) for r in ROUTES])), 2)


if __name__ == '__main__':
    unittest.main()
