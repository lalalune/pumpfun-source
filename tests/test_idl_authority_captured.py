"""Captured-program checks for Pump `admin_set_idl_authority`.

Every case runs the captured `evidence/original/pump/deployed.so` on LiteSVM
against an account at Pump's canonical IDL address
(`create_with_seed(empty-seed PDA, "anchor:idl", pump)`), owned by the System
Program, by Pump or by another program, at many sizes and balances. The same
inputs go to `programs/pump/recovered/idl_authority_host.rs`. The error, the
signed lamport deltas of the IDL account and `authority`, the resized data
(discriminator, new authority, the untouched `data_len` and payload, zero
fill) and the `AdminSetIdlAuthorityEvent` bytes in the log and in the
`emit_cpi!` self-call must agree. This is matching behaviour on these inputs
only, not a byte-identity claim. Below 44 bytes LiteSVM fails reads of the
bytes the realloc just added; `scripts/pump_idl_authority_surfpool.py` records
that Surfpool differs there, so those cases pin the LiteSVM outcome only.
`scripts/pump_idl_authority_differential.py`
(and its Surfpool variant) compares candidate builds with the captured
program; this test pins the outcomes to a model instead and does not read
`research/`.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
PUMP_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/idl_authority_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
OTHER_PROGRAM = Pubkey.from_bytes(bytes([12]) * 32)
INSTRUCTION = next(i for i in IDL['instructions'] if i['name'] == 'admin_set_idl_authority')
GLOBAL_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'Global')
EVENT_DISC = next(bytes(e['discriminator']) for e in IDL['events'] if e['name'] == 'AdminSetIdlAuthorityEvent')
IDL_ACCOUNT_DISC = hashlib.sha256(b'internal:IdlAccount').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
PAYER = Keypair.from_seed(bytes([201]) * 32)
AUTHORITY = Keypair.from_seed(bytes([202]) * 32)
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
PROGRAM_SIGNER = Pubkey.find_program_address([], PUMP)[0]
IDL_ADDRESS = Pubkey.create_with_seed(PROGRAM_SIGNER, 'anchor:idl', PUMP)
WRONG_ADDRESS = Pubkey.from_bytes(bytes([55]) * 32)
NEW_AUTHORITY = Pubkey.from_bytes(bytes([77]) * 32)
OLD_AUTHORITY = Pubkey.from_bytes(bytes([66]) * 32)
AUTHORITY_LAMPORTS = 10**10
FLAGS = ('signed', 'authority_ok', 'address_ok', 'program_signer_ok', 'authority_writable')
IDL_SIZE = 10_240


def rent(size):
    return (size + 128) * 6_960


def case(bad=(), writable=False, owner='p', size=IDL_SIZE, lamports=None, disc=True, data_len=5):
    flags = {name: name not in bad for name in FLAGS}
    flags['authority_writable'] = writable
    if lamports is None:
        lamports = rent(max(size, IDL_SIZE)) if owner != 's' else 5_000
    return dict(flags=flags, owner=owner, size=size, lamports=lamports, disc=disc, data_len=data_len)


def host_line(item):
    flags = ''.join('1' if item['flags'][name] else '0' for name in FLAGS)
    return f"{flags},{item['owner']},{item['size']},{item['lamports']},{int(item['disc'])}"


def idl_data(item):
    data = bytearray(i % 251 for i in range(item['size']))
    head = (IDL_ACCOUNT_DISC if item['disc'] else bytes(8)) + bytes(OLD_AUTHORITY) + struct.pack('<I', item['data_len'])
    data[:min(len(head), item['size'])] = head[:item['size']]
    return bytes(data)


def run_captured(item):
    flags = item['flags']
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(AUTHORITY.pubkey(), Account(AUTHORITY_LAMPORTS, b'', SYSTEM))
    global_data = bytearray(1088)
    global_data[:8] = GLOBAL_DISC
    global_data[8] = 1
    global_data[9:41] = bytes(AUTHORITY.pubkey() if flags['authority_ok'] else OLD_AUTHORITY)
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    target = IDL_ADDRESS if flags['address_ok'] else WRONG_ADDRESS
    owner = {'s': SYSTEM, 'p': PUMP, 'o': OTHER_PROGRAM}[item['owner']]
    if item['lamports'] or item['size']:
        vm.set_account(target, Account(item['lamports'], idl_data(item), owner))
    keys = {'authority': AUTHORITY.pubkey(), 'global': GLOBAL, 'idl_account': target, 'system_program': SYSTEM,
            'program_signer': PROGRAM_SIGNER if flags['program_signer_ok'] else EVENT_AUTHORITY,
            'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = []
    for account in INSTRUCTION['accounts']:
        signer = bool(account.get('signer')) and flags['signed']
        writable = bool(account.get('writable')) or (account['name'] == 'authority' and flags['authority_writable'])
        metas.append(AccountMeta(keys[account['name']], signer, writable))
    data = bytes(INSTRUCTION['discriminator']) + bytes(NEW_AUTHORITY)
    signers = [PAYER, AUTHORITY] if flags['signed'] else [PAYER]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], PAYER.pubkey(), signers,
                                           vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        err = result.err()
        code = getattr(getattr(err, 'err', None), 'code', None)
        return {'error': code if code is not None else str(err)}
    after = vm.get_account(target)
    return {
        'error': None,
        'idl_delta': (after.lamports if after else 0) - item['lamports'],
        'authority_delta': vm.get_account(AUTHORITY.pubkey()).lamports - AUTHORITY_LAMPORTS,
        'owner': after.owner if after and after.lamports else None,
        'data': bytes(after.data) if after and after.lamports else None,
        'events': [base64.b64decode(l[len('Program data: '):]) for l in result.logs() if l.startswith('Program data: ')],
        'cpi_events': [bytes(ix.instruction().data) for group in result.inner_instructions() for ix in group
                       if bytes(ix.instruction().data)[:8] == EVENT_CPI_TAG],
    }


NAMED = {'escalation': 'PrivilegeEscalation', 'invalid-argument': 'InvalidArgument',
         'invalid-realloc': 'InvalidRealloc', 'insufficient-rent': 'InsufficientFundsForRent'}


def fixed_cases():
    r = rent(IDL_SIZE)
    cases = [case(), case(writable=True)]
    # Pump-owned: grow, keep, shrink; the 44-byte floor; rent before/after.
    cases += [case(size=s) for s in (0, 7, 8, 40, 43, 44, 45, 100, 10_239, 10_241, 20_000, 30_000)]
    cases += [case(size=100, lamports=rent(100)), case(size=100, lamports=r - 1), case(size=100, lamports=r),
              case(size=10_240, lamports=10**6), case(size=10_240, lamports=r - 1), case(size=10_241, lamports=r),
              case(size=20_000, lamports=rent(20_000)), case(size=44, lamports=rent(44)),
              case(size=100, lamports=10**6), case(size=20_000, lamports=10**6), case(size=20_000, lamports=r - 1)]
    cases += [case(disc=False), case(disc=False, size=100, lamports=rent(100)), case(data_len=10**6),
              case(data_len=0)]
    cases += [case(size=s, disc=False) for s in (0, 7, 8, 43, 44)]
    # System-owned: the sweep needs a writable authority and an empty account.
    cases += [case(owner='s', lamports=l, size=0) for l in (0, 1, 5_000, 10**9)]
    cases += [case(owner='s', lamports=l, size=0, writable=True) for l in (0, 1, 5_000, 10**9)]
    cases += [case(owner='s', lamports=10**6, size=s, writable=True) for s in (1, 50, 10_240)]
    cases += [case(owner='s', lamports=10**6, size=50)]
    cases += [case(owner='o'), case(owner='o', size=7), case(owner='o', writable=True)]
    # Account checks and their order.
    cases += [case(bad=(name,)) for name in FLAGS[:4]]
    cases += [case(bad=pair) for pair in (('signed', 'authority_ok'), ('authority_ok', 'address_ok'),
                                          ('address_ok', 'program_signer_ok'), ('signed', 'address_ok'),
                                          ('authority_ok', 'program_signer_ok'))]
    cases += [case(bad=('authority_ok',), owner='s', size=0, lamports=0, writable=True),
              case(bad=('program_signer_ok',), owner='s', writable=True, size=0)]
    return cases


def random_cases():
    rng = random.Random(20261029)
    cases = []
    for _ in range(100):
        bad = tuple(n for n in FLAGS[:4] if rng.random() < 0.05)
        owner = rng.choice('ppps' + 'so'[rng.random() < 0.5])
        size = rng.choice([0, rng.randint(1, 60), rng.randint(60, 10_240), IDL_SIZE, rng.randint(10_241, 30_000)])
        if owner == 's':
            size = rng.choice([0, 0, 0, size])
        lamports = rng.choice([rent(max(size, IDL_SIZE)), rent(size), rent(IDL_SIZE) - rng.randint(1, 10**6),
                               rng.randint(0, 10**9)])
        if lamports == 0 and size:
            lamports = 1
        cases.append(case(bad, writable=rng.random() < 0.5, owner=owner, size=size, lamports=lamports,
                          disc=rng.random() < 0.85, data_len=rng.randint(0, 2**32 - 1)))
    return cases


class IdlAuthorityCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == PUMP_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'idl-authority-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if answer in NAMED:
            self.assertIn(NAMED[answer], str(captured['error']))
            return
        self.assertIsNone(captured['error'])
        if answer.startswith('swept,'):
            swept = int(answer[6:])
            # Signed deltas: the IDL address loses everything, authority gains it.
            self.assertEqual((captured['idl_delta'], captured['authority_delta']), (-swept, swept))
            self.assertIsNone(captured['data'])
            self.assertEqual((captured['events'], captured['cpi_events']), ([], []))
            return
        self.assertEqual(answer, 'rewritten')
        self.assertEqual((captured['idl_delta'], captured['authority_delta']), (0, 0))
        self.assertEqual(captured['owner'], PUMP)
        old = idl_data(item)
        kept = min(item['size'], IDL_SIZE)
        expected = (IDL_ACCOUNT_DISC + bytes(NEW_AUTHORITY) + old[40:kept] + bytes(IDL_SIZE - kept))
        self.assertEqual(captured['data'], expected)
        event = EVENT_DISC + bytes(NEW_AUTHORITY)
        self.assertEqual(captured['events'], [event])
        self.assertEqual(captured['cpi_events'], [EVENT_CPI_TAG + event])

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once the swept
        # amount, the outcome kind or the error code moves.
        samples = (case(), case(owner='s', size=0, lamports=5_000, writable=True), case(owner='o'),
                   case(owner='s', size=0))
        tampered = {'rewritten': ['swept,0', 'error:6010', 'insufficient-rent'],
                    'swept,5000': ['swept,4999', 'swept,5001', 'rewritten', 'escalation'],
                    'error:6010': ['error:6000', 'rewritten', 'invalid-realloc'],
                    'escalation': ['swept,5000', 'invalid-argument', 'error:6010']}
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            for text in tampered[answer]:
                with self.subTest(case=host_line(item), tampered=text):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = set(self.host_answers(fixed_cases()))
        kinds = {a.split(',')[0] for a in answers}
        self.assertEqual(kinds, {'rewritten', 'swept', 'escalation', 'invalid-argument', 'invalid-realloc',
                                 'insufficient-rent', 'error:2006', 'error:2012', 'error:3010', 'error:6000',
                                 'error:6010'})
        self.assertIn('swept,0', answers)
        self.assertIn('swept,1000000000', answers)


if __name__ == '__main__':
    unittest.main()
