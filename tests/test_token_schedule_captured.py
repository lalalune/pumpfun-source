"""Captured-program checks for the recovered Pump `admin_update_token_incentives`.

Every case runs Pump `admin_update_token_incentives` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token
and Associated Token programs, against a synthetic Global, a synthetic
GlobalVolumeAccumulator (GVA) and an existing incentive token account. The same
inputs go to `programs/pump/recovered/token_schedule_host.rs`, and the error
(or program panic), the stored GVA bytes and the
AdminUpdateTokenIncentivesEvent must agree. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
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
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/token_schedule_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = next(i for i in IDL['instructions'] if i['name'] == 'admin_update_token_incentives')

AUTHORITY = Keypair.from_seed(bytes([219]) * 32)
MINT = Pubkey.from_bytes(bytes([26]) * 32)
OLD_MINT = Pubkey.from_bytes(bytes([27]) * 32)
NOW = 1_700_000_000
DAY = 86_400
TOKEN_RENT = 2_039_280
I64 = 2**63 - 1
U64_MAX = 2**64 - 1


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


GLOBAL = pda(b'global')
GVA = pda(b'global_volume_accumulator')
EVENT_AUTHORITY = pda(b'__event_authority')
GVA_ATA = Pubkey.find_program_address([bytes(GVA), bytes(TOKEN), bytes(MINT)], ATA)[0]


def global_data():
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[9:41] = bytes(AUTHORITY.pubkey())
    return bytes(data)


def mint_data():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


DEFAULTS = dict(old_start=NOW - 5 * DAY, old_end=NOW + 20 * DAY, old_seconds=DAY,
                start=0, end=0, seconds=DAY, day=31, supply=0)


def case(**changes):
    return dict(DEFAULTS, **changes)


def gva_data(item):
    data = bytearray(ACCOUNT_DISC['GlobalVolumeAccumulator'])
    data += struct.pack('<qqq', item['old_start'], item['old_end'], item['old_seconds']) + bytes(OLD_MINT)
    data += struct.pack('<30Q', *(1000 + i for i in range(30))) + struct.pack('<30Q', *(5000 + i for i in range(30)))
    return bytes(data)


def args(item):
    return struct.pack('<qqqQQ', item['start'], item['end'], item['seconds'], item['day'], item['supply'])


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(AUTHORITY.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(GLOBAL, Account(10**9, global_data(), PUMP))
    vm.set_account(GVA, Account(10**9, gva_data(item), PUMP))
    vm.set_account(MINT, Account(10**9, mint_data(), TOKEN))
    vm.set_account(GVA_ATA, Account(TOKEN_RENT, token_data(MINT, GVA, 0), TOKEN))
    named = {'authority': AUTHORITY.pubkey(), 'global': GLOBAL, 'global_volume_accumulator': GVA, 'mint': MINT,
             'global_incentive_token_account': GVA_ATA, 'associated_token_program': ATA, 'system_program': SYSTEM,
             'token_program': TOKEN, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = [AccountMeta(named[a['name']], a.get('signer', False), a.get('writable', False)) for a in IX['accounts']]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(IX['discriminator']) + args(item), metas)],
                                           AUTHORITY.pubkey(), [AUTHORITY], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        if code:
            return {'error': int(code.group(1))}
        panicked = any('panicked' in line for line in result.meta().logs())
        return {'error': 'panic' if panicked else text}
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'gva': bytes(vm.get_account(GVA).data), 'events': events}


def host_line(item):
    fields = [gva_data(item).hex(), item['start'], item['end'], item['seconds'], item['day'], item['supply'],
              bytes(MINT).hex(), NOW]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    N, D = NOW, DAY
    cases = []
    add = lambda **k: cases.append(case(**k))
    # Only the day length and mint change.
    add()
    for seconds in (0, 1, -1, 3600, I64):
        add(seconds=seconds)
    add(start=N + 10, end=0)
    add(start=0, end=N + 10)
    # Time range: start, end, size limit (inclusive 30 days - 1 second).
    add(start=N - 5 * D, end=N + 24 * D)
    add(start=N + 10, end=N + 10 + 29 * D)
    add(start=N, end=N + D)
    add(start=N - 1, end=N + D)
    add(start=N + 1, end=N + 2)
    add(start=N - 5 * D, end=N)
    add(start=N - 5 * D, end=N + 1)
    add(start=N + 100, end=N + 100)
    add(start=N + 100, end=N + 99)
    add(start=N + 10, end=N + 10 + 30 * D)
    add(start=N + 10, end=N + 10 + 30 * D - 1)
    add(start=N + 10, end=N + 10 + 30 * D - 1, seconds=D - 1)
    add(start=N + 10, end=N + 20, seconds=0)
    add(start=N + 10, end=N + 20, seconds=-5)
    add(start=N + 10, end=N + 10 + 30, seconds=1)
    add(start=N + 10, end=N + 10 + 29, seconds=1)
    add(start=N + 10, end=I64, seconds=I64)
    add(start=N + 10, end=N + 20, seconds=I64 // 29)
    add(start=N - 5 * D, end=N + 1 * D)
    add(start=N - 5 * D, end=N + 2 * D, seconds=2 * D)
    add(start=N - 5 * D, end=N + D, seconds=D // 2)
    add(old_start=N - 5 * D - 7, start=N - 5 * D - 7, end=N + D)
    # Token supply before the start.
    for day in (0, 3, 25, 26, 29, 30, 2**64 - 1):
        add(old_start=N + 100, old_end=N + 100 + 25 * D, supply=7, day=day)
    add(old_start=N + 100, old_end=N + 100 + 40 * D, supply=7, day=30)
    add(old_start=N + 100, old_end=N + 99, supply=7, day=3)
    add(old_start=N + 100, supply=7, day=3, seconds=0)
    # Token supply inside the range.
    for day in (0, 4, 5, 6, 25, 26, 29, 30, 99):
        add(supply=7, day=day)
    add(supply=U64_MAX, day=10)
    add(old_end=N, supply=7, day=10)
    add(old_end=N - 1, supply=7, day=10)
    add(old_end=N - 1, supply=7, day=10, start=N - 5 * D, end=N + 2 * D)
    add(old_start=N, supply=7, day=0)
    add(old_end=N + 40 * D, supply=7, day=99)
    add(supply=7, day=10, seconds=0)
    add(supply=7, day=10, seconds=-D)
    add(old_start=-5, supply=7, day=10)
    # Range and supply together, each against the new range.
    add(start=N + 10, end=N + 10 + 3 * D, supply=9, day=2)
    add(start=N + 10, end=N + 10 + 3 * D, supply=9, day=4)
    add(start=N + 10, end=N + 10 + 3 * D, supply=9, day=30)
    add(start=N - 5 * D, end=N + 10 * D, supply=9, day=30)
    add(start=N - 5 * D, end=N + 10 * D, supply=9, day=16)
    return cases


def random_cases(count=60, seed=3521):
    rng = random.Random(seed)
    N, D = NOW, DAY
    cases = []
    for _ in range(count):
        seconds = rng.choice((D, D, 3600, rng.randrange(1, 2 * D), 0, -rng.randrange(1, D)))
        old_start = N + rng.randrange(-20 * D, 5 * D)
        old_end = old_start + rng.randrange(-D, 40 * D)
        start = rng.choice((0, old_start, N + rng.randrange(-D, 3 * D)))
        end = rng.choice((0, start + rng.randrange(-D, 31 * max(seconds, 1)), N + rng.randrange(-D, 30 * D)))
        cases.append(case(old_start=old_start, old_end=old_end, old_seconds=rng.choice((D, seconds)), start=start,
                          end=end, seconds=seconds, day=rng.choice((rng.randrange(0, 30), 30, rng.randrange(0, 2**64))),
                          supply=rng.choice((0, rng.randrange(1, 10**12)))))
    return cases


class TokenScheduleCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'token-schedule-host'
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
        if answer == 'panic':
            self.assertEqual(captured['error'], 'panic')
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        _, gva_hex, event_hex = answer.split(',')
        self.assertEqual(captured['gva'].hex(), gva_hex)
        self.assertEqual([e.hex() for e in captured['events']], [event_hex])

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

    def test_checker_rejects_a_changed_day(self):
        # Negative control: a passing supply update must fail once the stored
        # supply of another day changes.
        item = case(supply=7, day=99)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(answer, captured)
        stored = bytearray(captured['gva'])
        stored[64 + 8 * 4] ^= 1
        with self.assertRaises(AssertionError):
            self.assert_matches(answer, dict(captured, gva=bytes(stored)))

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'panic', 'error:6031', 'error:6032', 'error:6033', 'error:6034', 'error:6035', 'error:6036',
            'error:6037', 'error:6038',
        })


if __name__ == '__main__':
    unittest.main()
