"""Captured-program checks for the account admission of `distribute_fee_to_holders`.

Every case runs `distribute_fee_to_holders` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs: on the SOL path with no source account, on
a wrapped-SOL source, and on an SPL Token quote. One account set is the expected one
from `tests/test_holder_distribution_token_captured.py`, with two recipients. A case
changes it by one, two or three faults: wrong address, owner, data, mutability,
signature, program or stored field.

The same faults go to `programs/pump/recovered/holder_distribution_admission_host.rs`,
and the error, or the event count, the PDA's lamports and the source's tokens, must
agree. This shows matching behavior on these inputs only; it is not a byte-identity
claim.
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_holder_distribution_token_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/holder_distribution_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([69]) * 32)
ROUTES = ('native', 'wrapped', 'token')
IX = base.IX
NAMES = [a['name'] for a in IX['accounts']]
SLOT_FAULTS = {
    'global': ('key', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'holder_reward_claim_authority': ('unsigned', 'readonly'),
    'mint': ('key', 'owner', 'short', 'missing'),
    'holder_rewards': ('key', 'readonly', 'owner', 'data', 'missing'),
    'holder_rewards_token_account': ('key', 'readonly', 'none', 'owner', 'short', 'mintdata', 'ownerdata', 't22', 'missing'),
    'quote_mint': ('other', 'owner', 'short', 'missing'),
    'quote_token_program': ('key', 't22'),
    'associated_token_program': ('key',),
    'system_program': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'token'),
}
HOOKS = {'h.authority': {'authority_ok': False}, 'h.slots': {'accounts': 3}, 'h.over': {'entries': 'over'},
         'h.empty': {'entries': 'empty'}, 'h.lastwrong': {'entries': 'lastwrong'}}
ENTRIES = {'plain': ((0, 1000, 'e'), (1, 2000, 'n')), 'over': ((0, 1000, 'e'), (1, 10**12, 'n')), 'empty': (),
           'lastwrong': ((0, 1000, 'e'), (1, 2000, 'x'))}
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'ExternalAccountLamportSpend': 'external_lamport_spend',
           'ExternalAccountDataModified': 'external_data_modified', 'InvalidArgument': 'invalid_argument',
           'MissingAccount': 'missing_account', 'IncorrectProgramId': 'incorrect_program_id',
           'PrivilegeEscalation': 'privilege_escalation', 'ReadonlyLamportChange': 'readonly_lamports',
           'ReadonlyDataModified': 'readonly_data', 'InsufficientFundsForRent': 'rent', 'InvalidAccountOwner': 'invalid_owner',
           'IllegalOwner': 'illegal_owner'}


def faults_of():
    return [f'{slot}.{kind}' for slot in NAMES for kind in SLOT_FAULTS[slot]] + list(HOOKS)


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


def global_data(authority_ok):
    data = bytearray(1088)
    data[:8] = base.GLOBAL_DISC
    data[8] = 1
    data[1054:1086] = bytes(base.AUTHORITY.pubkey() if authority_ok else base.ELSEWHERE)
    data[1086] = 1
    return bytes(data)


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        self.vm.add_program_from_file(base.TOKEN, base.TOKEN_ELF)
        self.vm.add_program_from_file(base.TOKEN_2022, base.TOKEN_2022_ELF)
        self.vm.add_program_from_file(base.ATA_PROGRAM, base.ATA_ELF)
        self.vm.set_clock(base.Clock(100, base.NOW, 0, 0, base.NOW))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        over = {}
        for fault in faults:
            over.update(HOOKS.get(fault, {}))
        native = route != 'token'
        mint = base.WSOL if native else base.STABLE
        entries = ENTRIES[over.pop('entries', 'plain')]
        source = {'native': '-', 'wrapped': '111:5000', 'token': '111:1000000'}[route]
        item = base.case(*entries, native=native, source=source, **over)
        self.put(base.PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        source_key = base.ata(base.REWARDS, mint, base.TOKEN)
        self.stale.append(base.REWARDS)  # a close can bring it back when a fault removed it
        keys = {'global': base.GLOBAL, 'holder_reward_claim_authority': base.AUTHORITY.pubkey(), 'mint': base.MINT,
                'holder_rewards': base.REWARDS, 'holder_rewards_token_account': source_key if source != '-' else base.PUMP,
                'quote_mint': mint, 'quote_token_program': base.TOKEN, 'associated_token_program': base.ATA_PROGRAM,
                'system_program': base.SYSTEM, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        accounts = {
            base.GLOBAL: Account(10**9, global_data(item['authority_ok']), base.PUMP),
            base.AUTHORITY.pubkey(): Account(10**10, b'', base.SYSTEM),
            base.MINT: Account(1_461_600, base.mint_data(), base.TOKEN),
            mint: Account(1_461_600, base.mint_data(), base.TOKEN),
            base.OTHER_MINT: Account(1_461_600, base.mint_data(), base.TOKEN),
            base.REWARDS: Account(item['lamports'], b'', base.SYSTEM),
        }
        for wallet in base.WALLETS.values():
            accounts[wallet] = Account(base.WALLET_LAMPORTS, b'', base.SYSTEM)
            self.stale.append(base.ata(wallet, mint, base.TOKEN))
        if source != '-':
            amount = int(source.split(':')[1])
            accounts[source_key] = Account(base.TOKEN_RENT + (amount if native else 0),
                                           base.token_account(mint, base.REWARDS, amount, native), base.TOKEN)
        read_only, unsigned = set(), False
        for fault in faults:
            slot, kind = fault.split('.')
            if slot == 'h':
                continue
            key = keys[slot]
            present = accounts.get(key)
            if kind == 'readonly':
                read_only.add(slot)
            elif kind == 'unsigned':
                unsigned = True
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES.index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif kind == 'none':
                keys[slot] = base.PUMP
            elif kind == 'other':
                keys[slot] = base.OTHER_MINT
            elif kind == 'token':
                keys[slot] = base.TOKEN
            elif kind == 't22' and slot == 'quote_token_program':
                keys[slot] = base.TOKEN_2022
            elif kind == 'missing':
                accounts.pop(key, None)
            elif present is None:
                continue
            elif kind == 'owner':
                accounts[key] = Account(present.lamports, bytes(present.data), ALIEN)
            elif kind == 't22':
                accounts[key] = Account(present.lamports, bytes(present.data), base.TOKEN_2022)
            elif kind == 'short':
                accounts[key] = Account(present.lamports, bytes(4), present.owner)
            elif kind == 'trunc':
                accounts[key] = Account(present.lamports, bytes(present.data)[:8], present.owner)
            elif kind == 'disc':
                accounts[key] = rewrite(present, 0, bytes(8))
            elif kind == 'data':
                accounts[key] = Account(present.lamports, bytes(40), present.owner)
            elif len(present.data) == 165:
                accounts[key] = rewrite(present, 0 if kind == 'mintdata' else 32, bytes([9]) * 32)
        remaining = []
        for payee, _, state in item['entries']:
            wallet = base.WALLETS[payee]
            target = base.ata(wallet, mint, base.TOKEN)
            if state == 'e' and not native:
                accounts[target] = Account(base.TOKEN_RENT, base.token_account(mint, wallet, 0), base.TOKEN)
            if state == 'x':
                target = base.ata(wallet, base.OTHER_MINT, base.TOKEN)
            remaining += [AccountMeta(wallet, False, True), AccountMeta(target, False, True)]
        remaining += [AccountMeta(base.ELSEWHERE, False, True)] * max(0, item['accounts'] - len(remaining))
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], a.get('signer', False) and not unsigned,
                             a.get('writable', False) and a['name'] not in read_only) for a in IX['accounts']]
        metas += remaining[:item['accounts']]
        data = (bytes(IX['discriminator']) + len(item['entries']).to_bytes(4, 'little')
                + b''.join(base.struct.pack('<Q', amount) for _, amount, _ in item['entries']))
        signers = [base.PAYER] + ([] if unsigned else [base.AUTHORITY])
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(base.PUMP, data, metas)],
                                               base.PAYER.pubkey(), signers, self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        rewards = self.vm.get_account(keys['holder_rewards'])
        held = self.vm.get_account(keys['holder_rewards_token_account'])
        amount = int.from_bytes(bytes(held.data)[64:72], 'little') if held and len(held.data) == 165 and held.lamports else 0
        return f'ok,{events},{rewards.lamports if rewards else 0},{amount}'


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1500, seed=4196):
    rng = random.Random(seed)
    cases = []
    for route in rng.choices(ROUTES, k=count):
        faults = faults_of()
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    return cases


def host_line(route, faults):
    return ' '.join((route,) + faults)


class HolderDistributionAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'holder-distribution-admission-host'
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
                    self.run_cases([('token', ())])
        self.assertEqual(answers([('token', ())]), [self.harness.run('token', ())])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (1, 2000, 2006, 2014, 2015, 2021, 3001, 3002, 3003, 3007, 3008, 3010, 3012,
                                                 6000, 6085, 6087)}
                         | {'error:invalid_account_data', 'error:invalid_argument', 'error:external_lamport_spend',
                            'error:missing_account'})
        self.assertLessEqual({'ok,1,999997000,0', 'ok,1,1002041280,0', 'ok,1,1000000000,997000'}, answers)


if __name__ == '__main__':
    unittest.main()
