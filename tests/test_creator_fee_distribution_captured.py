"""Captured-program checks for the recovered Pump creator-fee distribution.

Every case runs Pump `distribute_creator_fees` and
`get_minimum_distributable_fee` from the captured
`evidence/original/pump/deployed.so` on LiteSVM against synthetic mint,
bonding-curve, pump_fees SharingConfig, creator-vault and shareholder
accounts. The same inputs go to
`programs/pump/recovered/creator_fee_distribution_host.rs`, and the error,
signed lamport movements, return data and DistributeCreatorFeesEvent must
agree. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_fee_distribution_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}

PAYER = Keypair.from_seed(bytes([221]) * 32)
MINT = Pubkey.from_bytes(bytes([31]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([32]) * 32)
ADMIN = Pubkey.from_bytes(bytes([33]) * 32)
OTHER = Pubkey.from_bytes(bytes([34]) * 32)
HOLDERS = [Pubkey.from_bytes(bytes([60 + i]) * 32) for i in range(8)]


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


CURVE = pda([b'bonding-curve', bytes(MINT)])
SHARING = pda([b'sharing-config', bytes(MINT)], FEES)
VAULT = pda([b'creator-vault', bytes(SHARING)])
EVENT_AUTHORITY = pda([b'__event_authority'])
TX_FEE = 5000
ZERO_RENT = 890_880
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1


def rent(data_len):
    return (128 + data_len) * 6960


def mint_data():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, 10**9, 10**15)
    data[49:81] = bytes(SHARING if item['curve_creator'] == 'sharing' else OTHER)
    if item['curve_quote']:
        data[83:115] = bytes(OTHER_MINT)
    struct.pack_into('<Q', data, 125, item['creator_fee'])
    return bytes(data)


def holder_address(i, h):
    return PUMP if h['key'] == 'program' else HOLDERS[i]


def shareholders_bytes(item):
    return b''.join(bytes(holder_address(i, h)) + struct.pack('<H', h['bps']) for i, h in enumerate(item['holders']))


def sharing_data(item):
    holders = item['holders']
    return (ACCOUNT_DISC['SharingConfig'] + bytes([255, 1, int(item['active'])])
            + bytes(MINT if item['config_mint'] == 'mint' else OTHER_MINT) + bytes(ADMIN) + bytes([0])
            + struct.pack('<I', len(holders)) + shareholders_bytes(item))


def holder(bps, lamports=10**9, data_len=0, key='own'):
    # key: 'own' (the configured address), 'other' (a different account in its
    # slot) or 'program' (the configured address is the executable Pump program).
    return dict(bps=bps, lamports=lamports, data_len=data_len, key=key)


DEFAULTS = dict(op='distribute', vault=ZERO_RENT + 10**9, holders=None, active=True, creator_fee=0,
                curve_creator='sharing', curve_quote=False, config_mint='mint', remaining=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['holders'] is None:
        item['holders'] = [holder(5000), holder(3000), holder(2000)]
    if item['remaining'] is None:
        item['remaining'] = len(item['holders'])
    return item


def holder_key(i, h):
    return OTHER if h['key'] == 'other' else holder_address(i, h)


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(MINT, Account(10**9, mint_data(), TOKEN))
    vm.set_account(CURVE, Account(10**9, curve_data(item), PUMP))
    vm.set_account(SHARING, Account(10**9, sharing_data(item), FEES))
    if item['vault']:
        vm.set_account(VAULT, Account(item['vault'], b'', SYSTEM))
    recipients = []
    for i, h in enumerate(item['holders'][:item['remaining']]):
        key = holder_key(i, h)
        recipients.append(key)
        if h['lamports'] and h['key'] == 'own':
            vm.set_account(key, Account(h['lamports'], bytes(h['data_len']), SYSTEM))
    names = {'mint': MINT, 'bonding_curve': CURVE, 'sharing_config': SHARING, 'creator_vault': VAULT,
             'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    ix = IX['distribute_creator_fees' if item['op'] == 'distribute' else 'get_minimum_distributable_fee']
    metas = [AccountMeta(names[a['name']], False, a.get('writable', False)) for a in ix['accounts']]
    metas += [AccountMeta(key, False, True) for key in recipients]
    watched = [PAYER.pubkey(), VAULT] + recipients
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    # Signed after - before for every watched account.
    delta = [lamports(k) - b for k, b in zip(watched, before)]
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'payer': delta[0], 'vault': delta[1], 'holders': delta[2:],
            'events': events, 'return_data': bytes(result.return_data().data)}


def slot(i, h, item):
    if i >= item['remaining']:
        return '-'
    if h['key'] == 'other':
        return 'wrong'
    if h['key'] == 'program':
        return 'exec'
    return f"{h['lamports']}/{h['data_len'] if h['lamports'] else 0}"


def host_line(item):
    holders = ';'.join(f"{h['bps']}:{slot(i, h, item)}" for i, h in enumerate(item['holders']))
    fields = [item['op'], item['vault'], int(item['active']), item['creator_fee'], int(item['curve_creator'] == 'sharing'),
              int(item['curve_quote']), int(item['config_mint'] == 'mint'), holders]
    return ','.join(str(f) for f in fields)


def distribute_payload(item, distributed):
    return (struct.pack('<q', TIMESTAMP) + bytes(MINT) + bytes(CURVE) + bytes(SHARING) + bytes(ADMIN)
            + struct.pack('<I', len(item['holders'])) + shareholders_bytes(item) + struct.pack('<Q', distributed)
            + bytes(SYSTEM))


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    H = holder
    for op in ('distribute', 'minimum'):
        add(op=op)
        # Vault balance around the zero-byte reserve.
        for vault in (0, 1, ZERO_RENT - 1, ZERO_RENT, ZERO_RENT + 1, ZERO_RENT + 9_999, ZERO_RENT + 10_000, U64 // 10_000):
            add(op=op, vault=vault)
        add(op=op, vault=U64 // 10_000 + 1)
        add(op=op, vault=U64)
        # Account and config checks, and their order.
        add(op=op, active=False)
        add(op=op, creator_fee=1)
        add(op=op, active=False, creator_fee=1)
        add(op=op, curve_creator='other')
        add(op=op, curve_quote=True)
        add(op=op, curve_quote=True, curve_creator='other')
        add(op=op, config_mint='other')
        add(op=op, curve_creator='other', config_mint='other')
        add(op=op, creator_fee=1, holders=[H(5000), H(5000, key='other')])
        # Per-shareholder checks, in slot order.
        add(op=op, holders=[H(5000), H(5000, key='other')])
        add(op=op, holders=[H(5000), H(5000, key='program')])
        add(op=op, holders=[H(5000), H(0)])
        add(op=op, holders=[H(5000, key='other'), H(0)])
        add(op=op, holders=[H(0, key='program')])
        add(op=op, holders=[H(0, key='other')])
        add(op=op, remaining=2)
        add(op=op, remaining=0)
        add(op=op, holders=[H(5000), H(5000, key='other')], vault=U64)
        add(op=op, holders=[])
        add(op=op, holders=[H(10_000)])
        add(op=op, holders=[H(1)], vault=ZERO_RENT + 9_999)
        add(op=op, holders=[H(1)] * 8, vault=ZERO_RENT + 10**9)
        add(op=op, holders=[H(3333), H(3333), H(3334)], vault=ZERO_RENT + 10**9 + 7)
        # Rent thresholds: ceil(deficit * 10000 / bps) against the distributable lamports.
        for extra in (-1, 0, 1):
            add(op=op, holders=[H(10_000, lamports=0)], vault=2 * ZERO_RENT + extra)
            add(op=op, holders=[H(7, lamports=0), H(9_993)], vault=ZERO_RENT + 1_272_685_715 + extra)
            add(op=op, holders=[H(3000, lamports=0), H(7000)], vault=ZERO_RENT + 2_969_600 + extra)
            add(op=op, holders=[H(6000), H(4000, lamports=1, data_len=10)], vault=ZERO_RENT + 2_401_198 + extra)
        add(op=op, holders=[H(10_000, lamports=890_000)], vault=ZERO_RENT + 880)
        add(op=op, holders=[H(10_000, lamports=890_000)], vault=ZERO_RENT + 879)
        add(op=op, holders=[H(7, lamports=0), H(9_993, lamports=5, data_len=3)], vault=100)
        # Shares above 100% are not rejected here.
        add(op=op, holders=[H(10_001)])
        add(op=op, holders=[H(10_000), H(1)], vault=ZERO_RENT + 8_908_800_000)
        add(op=op, holders=[H(10_000), H(1)], vault=ZERO_RENT + 8_908_800_001)
        add(op=op, holders=[H(10_000), H(2)], vault=ZERO_RENT + 8_908_800_000)
        add(op=op, holders=[H(6000), H(5000)])
        add(op=op, holders=[H(65_535), H(65_535)], vault=ZERO_RENT + 10**6)
    return cases


def random_cases(count=80, seed=1640):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.randrange(0, 8)
        cut = sorted(rng.sample(range(1, 10_000), n - 1)) if n > 1 else []
        shares = [b - a for a, b in zip([0] + cut, cut + [10_000])] if n else []
        holders = []
        for bps in shares:
            lamports = rng.choice((10**9, 0, rng.randrange(1, 2 * ZERO_RENT), rng.randrange(1, 5 * 10**6)))
            data_len = rng.choice((0, 0, 0, rng.randrange(1, 200)))
            key = rng.choice(('own',) * 30 + ('other', 'program'))
            if rng.random() < 0.03:
                bps = rng.choice((0, 10_001, 65_535))
            holders.append(holder(bps, lamports, data_len, key))
        vault = rng.choice((0, rng.randrange(0, 2 * ZERO_RENT), ZERO_RENT + rng.randrange(0, 10**7),
                            ZERO_RENT + rng.randrange(0, 10**12)))
        cases.append(case(op=rng.choice(('distribute', 'distribute', 'minimum')), holders=holders, vault=vault,
                          active=rng.random() < 0.93, creator_fee=0 if rng.random() < 0.93 else rng.randrange(1, 10**6),
                          curve_creator='sharing' if rng.random() < 0.95 else 'other',
                          curve_quote=rng.random() < 0.04, config_mint='mint' if rng.random() < 0.96 else 'other',
                          remaining=len(holders) if rng.random() < 0.95 else rng.randrange(0, len(holders) + 1)))
    return cases


class CreatorFeeDistributionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-fee-distribution-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, item, answer):
        self.assert_matches(item, answer, run_captured(item))

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['payer'], -TX_FEE)
        fields = answer.split(',')
        if item['op'] == 'minimum':
            required, distributable, can = map(int, fields[1:])
            payload = struct.pack('<QQ?', required, distributable, bool(can))
            self.assertEqual((captured['vault'], captured['holders']), (0, [0] * item['remaining']))
            self.assertEqual(captured['return_data'], payload)
            self.assertEqual(captured['events'], [EVENT_DISC['MinimumDistributableFeeEvent'] + payload])
            return
        distributed, event = int(fields[1]), int(fields[2])
        transfers = [int(t) for t in fields[3].split(';') if t]
        # Signed after - before: the vault pays, each shareholder is credited.
        self.assertEqual(captured['vault'], -distributed)
        self.assertEqual(captured['holders'], transfers)
        payload = distribute_payload(item, distributed)
        self.assertEqual(captured['return_data'], payload)
        self.assertEqual(captured['events'], [EVENT_DISC['DistributeCreatorFeesEvent'] + payload] if event else [])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_balance_movements(self):
        # Negative control: a passing captured distribution must fail once the
        # vault debit or any shareholder credit is reversed.
        item = case(holders=[holder(5000), holder(3000), holder(2000)])
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        flips = [dict(captured, vault=-captured['vault'])]
        for i in range(3):
            holders = list(captured['holders'])
            holders[i] = -holders[i]
            flips.append(dict(captured, holders=holders))
        for flipped in flips:
            with self.subTest(flipped=(flipped['vault'], flipped['holders'])):
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {'ok', 'error:1', 'error:6004', 'error:6024', 'error:6027', 'error:6051', 'error:6052',
                                    'error:6053', 'error:6054', 'error:6055', 'error:6063', 'error:6095'})
        distribute = [a for c, a in zip(cases, answers) if c['op'] == 'distribute' and a.startswith('ok')]
        self.assertTrue(any(a.split(',')[2] == '0' for a in distribute))  # below the minimum
        self.assertTrue(any(a.split(',')[2] == '1' and a.split(',')[1] != '0' for a in distribute))
        minimum = [a for c, a in zip(cases, answers) if c['op'] == 'minimum' and a.startswith('ok')]
        self.assertEqual({a.split(',')[3] for a in minimum}, {'0', '1'})


if __name__ == '__main__':
    unittest.main()
