"""Captured-program checks for the account admission of the creator fee collection.

Every case runs `collect_creator_fee` or `collect_creator_fee_v2` from the
captured `evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL
Token and Associated Token programs. One account set is the expected one from
`tests/test_creator_fee_collect_captured.py`. A case changes it by one, two or
three faults: wrong address, owner, data, mutability or program. Some cases also
leave the transfer out, by emptying the vault or by a creator that cannot be
paid.

The same faults go to `programs/pump/recovered/collect_account_admission_host.rs`,
and the error, lamports, tokens and event count must agree. This shows matching
behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
import random
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
import test_creator_fee_collect_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = {
    base.PUMP_ELF: base.ELF_SHA256[base.PUMP_ELF],
    base.DEPS / 'spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    base.DEPS / 'associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/collect_account_admission_host.rs'

TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
VAULT = base.ZERO_RENT + 10**6
HANDLERS = {'v1': 'collect_creator_fee', 'v2_sol': 'collect_creator_fee_v2', 'v2_spl': 'collect_creator_fee_v2'}
NAMES = {op: [a['name'] for a in base.IX[name]['accounts']] for op, name in HANDLERS.items()}
TOKEN_FAULTS = ('key', 'readonly', 'owner', 'short', 'mintdata', 'ownerdata', 'frozen', 'missing')
SLOT_FAULTS = {
    'creator': ('readonly',),
    'creator_vault': ('key', 'readonly', 'owner', 'data0', 'missing'),
    'system_program': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'token'),
    'creator_token_account': TOKEN_FAULTS,
    'creator_vault_token_account': TOKEN_FAULTS,
    'quote_mint': ('key', 'owner', 'short', 'missing'),
    'quote_token_program': ('key', 't22'),
    'associated_token_program': ('key',),
}
HOOKS = ('h.fees', 'h.exec', 'h.empty')


def faults_of(op):
    return [f'{slot}.{kind}' for slot in NAMES[op] for kind in SLOT_FAULTS.get(slot, ())] + list(HOOKS)


def rewrite(account, start, value):
    data = bytearray(bytes(account.data))
    data[start:start + len(value)] = value
    return Account(account.lamports, bytes(data), account.owner)


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        for name, key in (('spl_token', base.TOKEN), ('associated_token', base.ATA)):
            self.vm.add_program_from_file(key, base.DEPS / name / 'deployed.so')
        self.vm.add_program_from_file(base.EXECUTABLE, base.DEPS / 'donation_relay/deployed.so')
        self.vm.set_clock(base.Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, op, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        self.put(base.PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        quote = base.WSOL if op == 'v2_sol' else base.QUOTE
        creator = base.EXECUTABLE if 'h.exec' in faults else base.CREATOR
        vault = base.pda([b'creator-vault', bytes(creator)])
        creator_ata = base.pda([bytes(creator), bytes(base.TOKEN), bytes(quote)], base.ATA)
        vault_ata = base.pda([bytes(vault), bytes(base.TOKEN), bytes(quote)], base.ATA)
        keys = {'creator': creator, 'creator_vault': vault, 'system_program': base.SYSTEM,
                'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP, 'creator_token_account': creator_ata,
                'creator_vault_token_account': vault_ata, 'quote_mint': quote, 'quote_token_program': base.TOKEN,
                'associated_token_program': base.ATA}
        empty = 'h.empty' in faults
        accounts = {vault: Account(base.ZERO_RENT if empty else VAULT, b'', base.SYSTEM)}
        if 'h.exec' not in faults:
            owner = base.FEES if 'h.fees' in faults else base.SYSTEM
            accounts[creator] = Account(10**9, b'', owner)
        if op != 'v1':
            accounts[quote] = Account(10**9, base.mint_data(9 if quote == base.WSOL else 6), base.TOKEN)
            accounts[vault_ata] = Account(base.TOKEN_RENT, base.token_data(quote, vault, 0 if empty else 10**6), base.TOKEN)
            accounts[creator_ata] = Account(base.TOKEN_RENT, base.token_data(quote, creator, 0), base.TOKEN)
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
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES[op].index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif kind == 'token':
                keys[slot] = base.TOKEN
            elif kind == 't22':
                keys[slot] = TOKEN22
            elif kind == 'missing':
                accounts.pop(key, None)
            elif present is None:
                continue  # the slot's other fault already took the account away
            elif kind == 'owner':
                accounts[key] = Account(present.lamports, bytes(present.data), ALIEN)
            elif kind == 'short':
                accounts[key] = Account(present.lamports, bytes(4), present.owner)
            elif kind == 'data0':
                accounts[key] = Account(present.lamports, bytes(40), present.owner)
            elif len(present.data) == 165:
                value = {'mintdata': (0, bytes([9]) * 32), 'ownerdata': (32, bytes([9]) * 32), 'frozen': (108, b'\x02')}
                accounts[key] = rewrite(present, *value[kind])
        for key, account in accounts.items():
            self.put(key, account)
        ix = base.IX[HANDLERS[op]]
        metas = [AccountMeta(keys[a['name']], False, a.get('writable', False) and a['name'] not in read_only)
                 for a in ix['accounts']]
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(ix['discriminator']), metas)],
                                               base.PAYER.pubkey(), [base.PAYER], self.vm.latest_blockhash())
        vault_ata_key, creator_ata_key = keys.get('creator_vault_token_account'), keys.get('creator_token_account')
        before = self.balances(keys['creator'], vault_ata_key, creator_ata_key)
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return f'error:{error_name(str(result.err()))}'
        after = self.balances(keys['creator'], vault_ata_key, creator_ata_key)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        return f'ok,{after[0] - before[0]},{before[1] - after[1]},{events}'

    def balances(self, creator, vault_ata, creator_ata):
        account = self.vm.get_account(creator)
        tokens = 0
        if vault_ata:
            token = self.vm.get_account(vault_ata)
            if token and len(token.data) >= 72:
                tokens = int.from_bytes(bytes(token.data)[64:72], 'little')
        return (account.lamports if account else 0), tokens


RUNTIME = {'ExternalAccountLamportSpend': 'external_lamport_spend', 'ExternalAccountDataModified': 'external_data_modified',
           'InvalidArgument': 'invalid_argument', 'MissingAccount': 'missing_account'}


def error_name(text):
    for name, short in RUNTIME.items():
        if name in text:
            return short
    return base.error_name(text)


def single_cases():
    return [(op, (fault,)) for op in HANDLERS for fault in [None] + faults_of(op) if fault] + [(op, ()) for op in HANDLERS]


def pair_cases():
    return [(op, pair) for op in HANDLERS for pair in itertools.combinations(faults_of(op), 2)]


def triple_cases(count=900, seed=2023):
    rng = random.Random(seed)
    cases = []
    for op in rng.choices(tuple(HANDLERS), k=count):
        faults = faults_of(op)
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((op, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(op, faults):
    return ' '.join((op,) + tuple(f.replace('program.token', 'program.key') for f in faults))


class CollectAccountAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'collect-account-admission-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.harness = Harness()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(op, faults) + '\n' for op, faults in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        wrong = []
        for (op, faults), answer in zip(cases, answers):
            captured = self.harness.run(op, faults)
            if captured != answer:
                wrong.append((op, faults, answer, captured))
        self.assertEqual(wrong[:40], [], f'{len(wrong)} of {len(cases)} differ')

    def test_single_faults_match_captured_program(self):
        self.run_cases(single_cases())

    def test_fault_pairs_match_captured_program(self):
        self.run_cases(pair_cases())

    def test_seeded_triples_match_captured_program(self):
        self.run_cases(triple_cases())

    def test_unchecked_program_slot_passes_without_an_event(self):
        for op in HANDLERS:
            for fault in ('program.key', 'program.token'):
                self.assertEqual(self.harness.run(op, (fault,)), 'error:missing_account')
                self.assertEqual(self.harness.run(op, (fault, 'h.empty')), 'ok,0,0,0')

    def test_checker_rejects_a_changed_answer(self):
        # Negative control: run_cases must fail when the host's answer changes.
        answers = self.host_answers
        for changed in ('error:2000', 'ok,1,0,1'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([('v1', ())])
        self.assertEqual(answers([('v1', ())]), [self.harness.run('v1', ())])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3, 4, 17, 3007, 3008, 3012, 6050)}
                         | {'error:invalid_account_data', 'error:external_lamport_spend', 'error:invalid_argument',
                            'error:external_data_modified', 'error:missing_account'})
        self.assertIn('ok,1000000,0,1', answers)
        self.assertIn('ok,0,1000000,1', answers)
        self.assertIn('ok,0,0,0', answers)


if __name__ == '__main__':
    unittest.main()
