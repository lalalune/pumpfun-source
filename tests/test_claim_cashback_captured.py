"""Captured-program checks for the recovered Pump `claim_cashback`.

Every case runs Pump `claim_cashback` from the captured
`evidence/original/pump/deployed.so` on LiteSVM against a synthetic
UserVolumeAccumulator (UVA) and user account. The same inputs go to
`programs/pump/recovered/claim_cashback_host.rs`, and the error, the lamport
movements, the stored UVA bytes and the ClaimCashbackEvent must agree. This
shows matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/claim_cashback_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
UVA_DISC = bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name'] == 'UserVolumeAccumulator'))
CLAIM_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'ClaimCashbackEvent'))
IX = next(i for i in IDL['instructions'] if i['name'] == 'claim_cashback')

PAYER = Keypair.from_seed(bytes([215]) * 32)
USER = Pubkey.from_bytes(bytes([21]) * 32)
OTHER_USER = Pubkey.from_bytes(bytes([22]) * 32)
TIMESTAMP = 1_700_000_000
TX_FEE = 5000
U64 = 2**64 - 1
RENT_PER_BYTE = 6960  # Rent::minimum_balance(len) == (128 + len) * 6960


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


EVENT_AUTHORITY = pda(b'__event_authority')


def uva_key(owner):
    return pda(b'user_volume_accumulator', bytes(owner))


def rent(size):
    return (128 + size) * RENT_PER_BYTE


DEFAULTS = dict(size=137, extra=1_000_000, lamports=None, owner='pump', disc=True, pda_of='user', stored_user='user',
                claimed=7_000, earned=9_000_000, user_lamports=10**9, user_writable=True, uva_writable=True,
                needs_claim=1, has_total=1)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['lamports'] is None:
        item['lamports'] = rent(item['size']) + item['extra']
    return item


def uva_data(item):
    data = bytearray((i * 37 + 11) % 256 for i in range(item['size']))
    head = (UVA_DISC if item['disc'] else bytes(8)) + bytes(USER if item['stored_user'] == 'user' else OTHER_USER)
    head += bytes([item['needs_claim']]) + struct.pack('<QQQq', 5, 6, 7, TIMESTAMP - 50) + bytes([item['has_total']])
    head += struct.pack('<QQQQ', item['earned'], item['claimed'], 11, 12)
    data[:min(len(head), item['size'])] = head[:item['size']]
    return bytes(data)


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    uva = uva_key(USER if item['pda_of'] == 'user' else OTHER_USER)
    if item['lamports']:
        vm.set_account(uva, Account(item['lamports'], uva_data(item), PUMP if item['owner'] == 'pump' else SYSTEM))
    if item['user_lamports']:
        vm.set_account(USER, Account(item['user_lamports'], b'', SYSTEM))
    named = {'user': USER, 'user_volume_accumulator': uva, 'system_program': SYSTEM,
             'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    writable = {'user': item['user_writable'], 'user_volume_accumulator': item['uva_writable']}
    metas = [AccountMeta(named[a['name']], False, writable.get(a['name'], False)) for a in IX['accounts']]
    watched = (USER, uva)
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(k) for k in watched]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(IX['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'delta': tuple(lamports(k) - b for k, b in zip(watched, before)),
            'uva': bytes(vm.get_account(uva).data), 'events': events}


def host_line(item):
    fields = [bytes(USER).hex(), int(item['user_writable']), item['lamports'], int(item['owner'] == 'pump'),
              int(item['pda_of'] == 'user'), int(item['uva_writable']), uva_data(item).hex(), TIMESTAMP]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    add()
    # Claim = UVA lamports above the rent minimum of its full data length.
    for extra in (0, 1, 2, 890_880, 10**12):
        add(extra=extra)
    for lamports in (1, 5, rent(137) - 1):
        add(lamports=lamports)
    for size in (106, 137, 138, 300, 1024):
        add(size=size)
        add(size=size, extra=0)
    add(earned=0)
    add(earned=U64, extra=12345)
    add(stored_user='other')
    # total_cashback_claimed overflow, checked only for a non-zero claim.
    add(claimed=U64 - 1_000_000)
    add(claimed=U64 - 999_999)
    add(claimed=U64, extra=0)
    add(claimed=U64, extra=1)
    add(claimed=U64 - 1, extra=1)
    # The user account: absent, or holding lamports already.
    add(user_lamports=0)
    add(user_lamports=0, extra=0)
    add(user_lamports=1)
    # UVA loading.
    add(lamports=0)
    add(owner='system')
    add(owner='system', extra=0)
    add(disc=False)
    for size in (0, 7, 8, 105):
        add(size=size, lamports=rent(size) + 1_000_000)
    add(needs_claim=2)
    add(needs_claim=0)
    add(has_total=2)
    add(has_total=0)
    # Account constraints and their order.
    add(user_writable=False)
    add(uva_writable=False)
    add(pda_of='other')
    add(user_writable=False, owner='system')
    add(user_writable=False, disc=False)
    add(user_writable=False, pda_of='other')
    add(uva_writable=False, pda_of='other')
    add(uva_writable=False, disc=False)
    add(user_writable=False, uva_writable=False)
    add(pda_of='other', lamports=0)
    return cases


def random_cases(count=60, seed=3520):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        size = rng.choice((106, 137, 137, 137, rng.randrange(106, 600), rng.randrange(0, 106)))
        lamports = rng.choice((rent(size) + rng.randrange(0, 10**10), rng.randrange(1, rent(size) + 2),
                               rent(size) + rng.randrange(0, 3)))
        earned = rng.choice((0, rng.randrange(0, 10**10), U64))
        claimed = rng.choice((0, rng.randrange(0, 10**12), U64 - rng.randrange(0, 10**10)))
        amount = max(0, lamports - rent(size))
        user_lamports = rng.choice((10**9, 0)) if amount == 0 or amount >= rent(0) else 10**9
        cases.append(case(size=size, lamports=lamports, earned=earned, claimed=claimed, user_lamports=user_lamports,
                          owner='pump' if rng.random() < 0.9 else 'system', disc=rng.random() < 0.95,
                          pda_of='user' if rng.random() < 0.9 else 'other', user_writable=rng.random() < 0.9,
                          uva_writable=rng.random() < 0.9, needs_claim=rng.choice((0, 1, 1, 1, 2))))
    return cases


class ClaimCashbackCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'claim-cashback-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        _, amount, uva_hex, event_hex = answer.split(',')
        self.assertEqual(captured['delta'], (int(amount), -int(amount)))
        self.assertEqual(captured['uva'].hex(), uva_hex)
        self.assertEqual([e.hex() for e in captured['events']], [] if event_hex == '-' else [event_hex])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=item, host=answer[:40]):
                self.assert_matches(answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_movement(self):
        # Negative control: a passing claim must fail once the lamport
        # movement is reversed or the stored claimed total changes.
        item = case()
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(answer, captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(answer, dict(captured, delta=tuple(-d for d in captured['delta'])))
        stored = bytearray(captured['uva'])
        stored[82] ^= 1
        with self.assertRaises(AssertionError):
            self.assert_matches(answer, dict(captured, uva=bytes(stored)))

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'error:2000', 'error:2006', 'error:3001', 'error:3002', 'error:3003', 'error:3007', 'error:3012',
            'error:6024',
        })


if __name__ == '__main__':
    unittest.main()
