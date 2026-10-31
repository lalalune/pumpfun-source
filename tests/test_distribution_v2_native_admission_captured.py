"""Captured-program checks for the account admission of native `distribute_creator_fees_v2`.

Every case runs `distribute_creator_fees_v2` on a native coin from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token and
Associated Token programs. One account set is the expected one from
`tests/test_creator_fee_distribution_captured.py`, with three shareholders. A case
changes it by one, two or three faults: wrong address, owner, data, mutability,
program or stored field.

The same faults go to `programs/pump/recovered/distribution_v2_native_admission_host.rs`,
and the error, or the lamports the vault paid and the event count, must agree. This
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_creator_fee_distribution_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'evidence/dependencies'
ELF_SHA256 = dict(base.ELF_SHA256)
ELF_SHA256[DEPS / 'spl_token/deployed.so'] = '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697'
ELF_SHA256[DEPS / 'associated_token/deployed.so'] = '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/distribution_v2_native_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([67]) * 32)
FEE_PAYER = Keypair.from_seed(bytes([242]) * 32)
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
ROUTES = ('native',)
IX = base.IX['distribute_creator_fees_v2']
NAMES = [a['name'] for a in IX['accounts']]
SLOT_FAULTS = {
    'payer': ('unsigned', 'readonly'),
    'mint': ('key', 'owner', 'short', 'missing'),
    'bonding_curve': ('key', 'owner', 'short', 'disc', 'missing'),
    'sharing_config': ('key', 'matched', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'creator_vault': ('key', 'readonly', 'owner', 'data', 'missing'),
    'system_program': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'token'),
    'creator_vault_quote_token_account': ('key', 'readonly', 'present'),
    'quote_mint': ('key', 'other', 'owner', 'short', 'missing'),
    'quote_token_program': ('key', 't22'),
    'associated_token_program': ('key',),
}
HOOKS = {'h.inactive': {'active': False}, 'h.unswept': {'creator_fee': 1}, 'h.creator': {'curve_creator': 'other'},
         'h.configmint': {'config_mint': 'other'}, 'h.noslots': {'remaining': 0}, 'h.quote': {'curve_quote': True}}
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'ExternalAccountDataModified': 'external_data_modified',
           'ExternalAccountLamportSpend': 'external_lamport_spend', 'InvalidArgument': 'invalid_argument'}


def base_token(mint, owner):
    return (bytes(mint) + bytes(owner) + bytes(8) + bytes(36) + bytes([1]) + bytes(20) + bytes(36))


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


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        for name, key in (('spl_token', base.TOKEN), ('associated_token', ATA)):
            self.vm.add_program_from_file(key, DEPS / name / 'deployed.so')
        self.vm.set_clock(base.Clock(100, base.TIMESTAMP, 0, 0, base.TIMESTAMP))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def run(self, route, faults):
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        over = {}
        for fault in faults:
            over.update(HOOKS.get(fault, {}))
        item = base.case(**over)
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        vault_ata = Pubkey.find_program_address([bytes(base.VAULT), bytes(base.TOKEN), bytes(WSOL)], ATA)[0]
        keys = {'payer': base.PAYER.pubkey(), 'mint': base.MINT, 'bonding_curve': base.CURVE,
                'sharing_config': base.SHARING, 'creator_vault': base.VAULT, 'system_program': base.SYSTEM,
                'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP,
                'creator_vault_quote_token_account': vault_ata, 'quote_mint': WSOL,
                'quote_token_program': base.TOKEN, 'associated_token_program': ATA}
        accounts = {
            base.PAYER.pubkey(): Account(10**12, b'', base.SYSTEM),
            base.MINT: Account(10**9, base.mint_data(), base.TOKEN),
            WSOL: Account(10**9, base.mint_data(), base.TOKEN),
            base.OTHER_MINT: Account(10**9, base.mint_data(), base.TOKEN),
            base.CURVE: Account(10**9, base.curve_data(item), base.PUMP),
            base.SHARING: Account(10**9, base.sharing_data(item), base.FEES),
            base.VAULT: Account(item['vault'], b'', base.SYSTEM),
        }
        remaining = []
        for i, h in enumerate(item['holders'][:item['remaining']]):
            address = base.holder_key(i, h)
            remaining.append(address)
            accounts[address] = Account(h['lamports'], b'', base.SYSTEM)
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
            elif kind == 'matched':
                # Another config the curve does name as its creator.
                keys[slot] = Pubkey.from_bytes(bytes([99]) * 32)
                accounts[keys[slot]] = accounts.pop(key)
                curve = accounts.get(keys['bonding_curve'])
                if curve and len(curve.data) == 166:
                    accounts[keys['bonding_curve']] = rewrite(curve, 49, bytes(keys[slot]))
            elif kind == 'other':
                # Another mint, and the vault's token account of that mint.
                keys[slot] = base.OTHER_MINT
                token_key = keys['creator_vault_quote_token_account']
                if token_key == vault_ata:
                    keys['creator_vault_quote_token_account'] = Pubkey.find_program_address(
                        [bytes(base.VAULT), bytes(base.TOKEN), bytes(base.OTHER_MINT)], ATA)[0]
                    if token_key in accounts:
                        accounts[keys['creator_vault_quote_token_account']] = accounts.pop(token_key)
            elif kind == 'token':
                keys[slot] = base.TOKEN
            elif kind == 't22':
                keys[slot] = TOKEN22
            elif kind == 'missing':
                accounts.pop(key, None)
            elif kind == 'present':
                accounts[key] = Account(10**7, base_token(WSOL, base.VAULT), base.TOKEN)
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
            elif kind == 'data':
                accounts[key] = Account(present.lamports, bytes(40), present.owner)
        for key, account in accounts.items():
            self.put(key, account)
        metas = [AccountMeta(keys[a['name']], a['name'] == 'payer' and not unsigned,
                             a.get('writable', False) and a['name'] not in read_only) for a in IX['accounts']]
        metas += [AccountMeta(key, False, True) for key in remaining]
        signers = [FEE_PAYER] if unsigned else [FEE_PAYER, base.PAYER]
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), Instruction(base.PUMP, bytes(IX['discriminator']) + bytes([0]), metas)],
            FEE_PAYER.pubkey(), signers, self.vm.latest_blockhash())
        source = keys['creator_vault']
        before = self.lamports(source)
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        return f'ok,{before - self.lamports(source)},{events}'


def single_cases():
    return [('native', (fault,)) for fault in faults_of()] + [('native', ())]


def pair_cases():
    return [('native', pair) for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1200, seed=4194):
    rng = random.Random(seed)
    faults = faults_of()
    # In the list's order, as the pairs are: a slot's later fault wins.
    return [('native', tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))) for _ in range(count)]


def host_line(route, faults):
    return ' '.join((route,) + faults)


class DistributionV2NativeAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'distribution-v2-native-admission-host'
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

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (2000, 2006, 3001, 3002, 3003, 3007, 3008, 3010, 3012, 6004, 6027, 6051,
                                                 6053, 6095)}
                         | {'error:invalid_account_data', 'error:invalid_argument', 'error:external_lamport_spend'})
        self.assertLessEqual({'ok,1000000000,1', 'ok,0,1'}, answers)


if __name__ == '__main__':
    unittest.main()
