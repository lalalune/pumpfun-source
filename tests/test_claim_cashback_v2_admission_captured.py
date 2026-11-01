"""Captured-program checks for the account admission of `claim_cashback_v2`.

Every case runs `claim_cashback_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token and
Associated Token programs. One account set is the expected one from
`tests/test_claim_cashback_v2_captured.py`, on the native or the token route. A
case changes it by one, two or three faults: wrong address, owner, data,
mutability or program.

The same faults go to
`programs/pump/recovered/claim_cashback_v2_admission_host.rs`, and the error,
lamports, tokens and event count must agree. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
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
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_claim_cashback_v2_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/claim_cashback_v2_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
ROUTES = ('native', 'token')
NAMES = [a['name'] for a in base.IX['accounts']]
TOKEN_STATE = ('owner', 'short', 'mintdata', 'ownerdata', 'frozen', 'missing')
SLOT_FAULTS = {
    'user': ('readonly',),
    'user_volume_accumulator': ('key', 'readonly', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'quote_mint': ('key', 'short', 'missing'),
    'quote_token_program': ('key', 'program'),
    'associated_token_program': ('key',),
    'associated_user_volume_accumulator': ('key', 'readonly') + TOKEN_STATE,
    'associated_quote_user': ('key', 'readonly') + TOKEN_STATE,
    'system_program': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'token'),
}
HOOKS = ('h.empty',)
EVENT = re.compile('^Program data: ')
RUNTIME = {'ExternalAccountDataModified': 'external_data_modified', 'InvalidAccountData': 'invalid_account_data'}


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
        self.vm.set_clock(base.Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
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
        validate_case(route, faults)
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        self.put(base.PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        item = base.case(native=route == 'native')
        mint = base.NATIVE_MINT if route == 'native' else base.QUOTE_MINT
        empty = 'h.empty' in faults
        uva_ata = base.ata(base.UVA, mint)
        user_ata = base.ata(base.USER, mint)
        keys = {'user': base.USER, 'user_volume_accumulator': base.UVA, 'quote_mint': mint,
                'quote_token_program': base.TOKEN, 'associated_token_program': base.ATA,
                'associated_user_volume_accumulator': uva_ata, 'associated_quote_user': user_ata,
                'system_program': base.SYSTEM, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        extra = 0 if empty else item['extra']
        accounts = {
            base.USER: Account(10**9, b'', base.SYSTEM),
            base.UVA: Account(base.rent(base.UVA_LEN) + extra, base.uva_data(item), base.PUMP),
            mint: Account(10**9, base.mint_data(), base.TOKEN),
            uva_ata: Account(base.TOKEN_RENT, base.token_data(mint, base.UVA, 0 if empty else 500_000), base.TOKEN),
            user_ata: Account(base.TOKEN_RENT, base.token_data(mint, base.USER, 3), base.TOKEN),
        }
        read_only = set()
        for fault in faults:
            slot, kind = fault.split('.')
            if slot == 'h':
                continue
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
            elif kind == 'program':
                keys[slot] = base.ATA
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
            elif len(present.data) == 165 or len(present.data) == base.TOKEN_RENT:
                value = {'mintdata': (0, bytes([9]) * 32), 'ownerdata': (32, bytes([9]) * 32), 'frozen': (108, b'\x02')}
                accounts[key] = rewrite(present, *value[kind])
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], False, a.get('writable', False) and a['name'] not in read_only)
                 for a in base.IX['accounts']]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(base.IX['discriminator']), metas)],
                                               base.PAYER.pubkey(), [base.PAYER], self.vm.latest_blockhash())
        source = keys['associated_user_volume_accumulator']
        before = self.lamports(keys['user']), self.tokens(source)
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if EVENT.match(line))
        return f"ok,{self.lamports(keys['user']) - before[0]},{before[1] - self.tokens(source)},{events}"


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1200, seed=3522):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(ROUTES, k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def validate_case(route, faults):
    allowed = set(faults_of())
    if (type(route) is not str or route not in ROUTES
            or not isinstance(faults, (tuple, list))
            or any(type(fault) is not str or fault not in allowed for fault in faults)):
        raise ValueError("unsupported admission route or fault")


def host_line(route, faults):
    validate_case(route, faults)
    return ' '.join((route,) + tuple(faults))


class ClaimCashbackV2AdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (base.IX["name"] != "claim_cashback_v2"
                or base.IX["discriminator"] != [122, 243, 204, 65, 94, 116, 29, 55]):
            raise AssertionError("unexpected captured instruction selector")
        for path, digest in ELF_SHA256.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError("captured ELF digest mismatch: " + str(path))
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'claim-cashback-v2-admission-host'
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
                    self.run_cases([('native', ())])
        self.assertEqual(answers([('native', ())]), [self.harness.run('native', ())])

    def test_rejects_malformed_host_and_vm_requests(self):
        for line in ('unrelated_route', 'native' + ' user.nonsense',
                     'native' + ' user_volume_accumulator.owner user_volume_accumulator.nonsense', ''):
            result = subprocess.run([str(self.host)], input=line + '\n', capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
        for route, faults in (('unrelated_route', ()), ('native', ('user.nonsense',))):
            with self.assertRaises(ValueError):
                host_line(route, faults)
            with self.assertRaises(ValueError):
                self.harness.run(route, faults)

    def test_missing_accounts_stay_missing_in_both_fault_orders(self):
        cases = []
        for kind in ('owner', 'short', 'disc', 'trunc'):
            faults = ('user_volume_accumulator.missing', f'user_volume_accumulator.{kind}')
            cases.extend((route, order) for route in ROUTES for order in (faults, faults[::-1]))
        self.assertEqual(self.host_answers(cases), ['error:3012'] * len(cases))
        for faults in (('quote_mint.missing', 'quote_mint.short'),
                       ('quote_mint.short', 'quote_mint.missing')):
            self.assertEqual(self.host_answers([('token', faults)]), ['error:6010'])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3, 4, 17, 3001, 3002, 3003, 3007, 3008, 3012, 6010, 6076)}
                         | {'error:invalid_account_data', 'error:external_data_modified'})
        self.assertLessEqual({'ok,1000000,0,1', 'ok,0,500000,1', 'ok,0,0,0'}, answers)


if __name__ == '__main__':
    unittest.main()
