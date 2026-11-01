"""Captured-program checks for the account admission of legacy `create`.

Every case runs `create` from the captured `evidence/original/pump/deployed.so` on
LiteSVM, with the captured Token Metadata, SPL Token and Associated Token programs.
One account set is the expected one from `tests/test_legacy_create_captured.py`. A
case changes it by one, two or three faults: wrong address, owner, data, mutability,
signature, program or an account that already exists.

The same faults go to `programs/pump/recovered/create_admission_host.rs`, and the
error, or the event count, the stored curve reserves and the minted amount, must
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
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_legacy_create_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'evidence/dependencies'
ELF_SHA256 = dict(base.ELF_SHA256)
ELF_SHA256[DEPS / 'spl_token/deployed.so'] = '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697'
ELF_SHA256[DEPS / 'associated_token/deployed.so'] = '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_admission_host.rs'

ALIEN = Pubkey.from_bytes(bytes([65]) * 32)
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
FEE_PAYER = Keypair.from_seed(bytes([238]) * 32)
OTHER_MINT = Keypair.from_seed(bytes([239]) * 32)
ROUTES = ('create',)
IX = base.CREATE
NAMES = [a['name'] for a in IX['accounts']]
SLOT_FAULTS = {
    'mint': ('other', 'unsigned', 'readonly', 'taken', 'funded'),
    'mint_authority': ('key',),
    'bonding_curve': ('key', 'readonly', 'taken', 'funded'),
    'associated_bonding_curve': ('key', 'readonly', 'taken', 'funded'),
    'global': ('key', 'owner', 'short', 'disc', 'trunc', 'missing'),
    'mpl_token_metadata': ('key',),
    'metadata': ('key', 'readonly', 'taken', 'funded'),
    'user': ('unsigned', 'readonly', 'poor'),
    'system_program': ('key',),
    'token_program': ('key', 't22'),
    'associated_token_program': ('key',),
    'rent': ('key',),
    'event_authority': ('key',),
    'program': ('key', 'token'),
}
HOOKS = {'h.badbool': {'faults': 'B'}, 'h.creator': {'creator_zero': 1}, 'h.name': {'name': 'x' * 33}}
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'BorshIoError': 'borsh', 'AccountNotFound': 'account_not_found',
           'MissingAccount': 'missing_account', 'IncorrectProgramId': 'incorrect_program_id',
           'PrivilegeEscalation': 'privilege_escalation', 'ExternalAccountDataModified': 'external_data_modified',
           'ReadonlyDataModified': 'readonly_data_modified', 'InvalidProgramArgument': 'invalid_argument',
           'InvalidArgument': 'invalid_argument', 'InvalidSeeds': 'invalid_seeds', 'InvalidAccountOwner': 'invalid_owner',
           'IllegalOwner': 'illegal_owner', 'InsufficientFunds': 'insufficient_funds',
           'UnsupportedProgramId': 'unsupported_program', 'NotEnoughAccountKeys': 'not_enough_keys',
           'AccountDataTooSmall': 'too_small', 'ReadonlyLamportChange': 'readonly_lamports', 'ProgramFailedToComplete': 'failed'}


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
        programdata = base.pda([bytes(base.PUMP)], base.UPGRADEABLE)
        elf = base.PUMP_ELF.read_bytes()
        self.vm.set_account(programdata, Account(10**10, base.struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf,
                                                 base.UPGRADEABLE, False))
        self.vm.set_account(base.PUMP, Account(10**9, base.struct.pack('<I', 2) + bytes(programdata), base.UPGRADEABLE, True))
        self.vm.add_program_from_file(base.METADATA, base.METADATA_ELF)
        for name, key in (('spl_token', base.TOKEN), ('associated_token', base.ATA)):
            self.vm.add_program_from_file(key, DEPS / name / 'deployed.so')
        self.vm.set_clock(Clock(1000, 0, 0, 0, base.TS))
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def run(self, route, faults):
        validate_case(route, faults)
        for key in self.stale + list(base.ACCOUNTS[name] for name in ('mint', 'bonding_curve', 'associated_bonding_curve', 'metadata')):
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        over = {}
        for fault in faults:
            over.update(HOOKS.get(fault, {}))
        item = base.case(**over)
        keys = dict(base.ACCOUNTS)
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', base.SYSTEM))
        accounts = {base.GLOBAL: Account(10**9, base.global_data(item), base.PUMP),
                    base.USER.pubkey(): Account(10**12, b'', base.SYSTEM)}
        mint_signer = base.MINT
        read_only, unsigned = set(), set()
        for fault in faults:
            slot, kind = fault.split('.')
            if slot == 'h':
                continue
            key = keys[slot]
            present = accounts.get(key)
            if kind == 'readonly':
                read_only.add(slot)
            elif kind == 'unsigned':
                unsigned.add(slot)
            elif kind == 'key':
                keys[slot] = Pubkey.from_bytes(bytes([100 + NAMES.index(slot)]) * 32)
                if present:
                    accounts[keys[slot]] = accounts.pop(key)
            elif kind == 'other':
                mint_signer = OTHER_MINT
                keys[slot] = OTHER_MINT.pubkey()
            elif kind == 'token':
                keys[slot] = base.TOKEN
            elif kind == 't22':
                keys[slot] = TOKEN22
            elif kind == 'taken':
                data, owner = {'mint': (bytes(82), base.TOKEN), 'bonding_curve': (bytes(166), base.PUMP),
                               'associated_bonding_curve': (bytes(165), base.TOKEN),
                               'metadata': (bytes(100), base.METADATA)}[slot]
                accounts[key] = Account(10**7, data, owner)
            elif kind == 'funded':
                accounts[key] = Account(10**7, b'', base.SYSTEM)
            elif kind == 'poor':
                accounts[key] = Account(1000, b'', base.SYSTEM)
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
        metas = [AccountMeta(keys[a['name']], a.get('signer', False) and a['name'] not in unsigned,
                             a.get('writable', False) and a['name'] not in read_only) for a in IX['accounts']]
        data = (bytes(IX['discriminator']) + base.borsh_string(item['name']) + base.borsh_string(item['symbol'])
                + base.borsh_string(item['uri']) + bytes(base.SYSTEM if item['creator_zero'] else base.CREATOR))
        signers = [FEE_PAYER] + ([] if 'user' in unsigned else [base.USER]) + ([] if 'mint' in unsigned else [mint_signer])
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(base.PUMP, data, metas)],
                                               FEE_PAYER.pubkey(), signers, self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result)
        events = sum(1 for line in result.logs() if line.startswith('Program data: '))
        curve = bytes(self.vm.get_account(keys['bonding_curve']).data)
        token = bytes(self.vm.get_account(keys['associated_bonding_curve']).data)
        reserves = int.from_bytes(curve[8:16], 'little')
        return f"ok,{events},{reserves},{int.from_bytes(token[64:72], 'little')}"


def single_cases():
    return [(route, (fault,)) for route in ROUTES for fault in faults_of()] + [(route, ()) for route in ROUTES]


def pair_cases():
    return [(route, pair) for route in ROUTES for pair in itertools.combinations(faults_of(), 2)]


def triple_cases(count=1000, seed=4192):
    rng = random.Random(seed)
    faults = faults_of()
    cases = []
    for route in rng.choices(ROUTES, k=count):
        # In the list's order, as the pairs are: a slot's later fault wins.
        cases.append((route, tuple(faults[i] for i in sorted(rng.sample(range(len(faults)), 3)))))
    # A funded `init` takes no lamports, so a `user` fault moves past what follows it.
    for route in ROUTES:
        for user in ('user.readonly', 'user.poor'):
            for later in ('bonding_curve.key', 'bonding_curve.taken', 'mint_authority.key'):
                cases.append((route, ('mint.funded', later, user)))
            for later in ('associated_bonding_curve.key', 'associated_bonding_curve.taken', 'mint_authority.key'):
                cases.append((route, ('mint.funded', 'bonding_curve.funded', later, user)))
            cases.append((route, ('mint.funded', 'bonding_curve.funded', 'associated_bonding_curve.funded', user)))
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


class CreateAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (base.CREATE["name"] != "create"
                or base.CREATE["discriminator"] != [24, 30, 200, 40, 5, 28, 7, 119]):
            raise AssertionError("unexpected captured instruction selector")
        for path, digest in ELF_SHA256.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise AssertionError("captured ELF digest mismatch: " + str(path))
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-admission-host'
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
                    self.run_cases([('create', ())])
        self.assertEqual(answers([('create', ())]), [self.harness.run('create', ())])

    def test_rejects_malformed_host_and_vm_requests(self):
        for line in ('unrelated_route', 'create' + ' user.nonsense',
                     'create' + ' global.owner global.nonsense', ''):
            result = subprocess.run([str(self.host)], input=line + '\n', capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')
        for route, faults in (('unrelated_route', ()), ('create', ('user.nonsense',))):
            with self.assertRaises(ValueError):
                host_line(route, faults)
            with self.assertRaises(ValueError):
                self.harness.run(route, faults)

    def test_missing_accounts_stay_missing_in_both_fault_orders(self):
        cases = []
        for kind in ('owner', 'short', 'disc', 'trunc'):
            faults = ('global.missing', f'global.{kind}')
            cases.extend(('create', order) for order in (faults, faults[::-1]))
        self.assertEqual(self.host_answers(cases), ['error:3012'] * len(cases))

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (0, 1, 11, 199, 2000, 2006, 3001, 3002, 3003, 3007, 3008, 3010, 3012,
                                                 3015, 6030)}
                         | {'error:privilege_escalation', 'error:missing_account', 'error:illegal_owner'})
        self.assertIn('ok,1,1073000000000000,1000000000000000', answers)


if __name__ == '__main__':
    unittest.main()
