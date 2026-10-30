"""Captured-program checks for the recovered Pump bonding-curve fee sweep.

Every case runs Pump `sweep_protocol_fee` or `sweep_creator_fee` from the
captured `evidence/original/pump/deployed.so` on LiteSVM, with the captured
SPL Token and Associated Token programs, against synthetic accounts for
native (SOL) and SPL-token quote curves. The same inputs go to
`programs/pump/recovered/sweep_fees_host.rs`, and the error, lamport and
token movements, stored fee buckets, and SweepBondingCurveFeeEvent must
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
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/sweep_fees_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
NATIVE_MINT = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
SWEEP_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'SweepBondingCurveFeeEvent'))

PAYER = Keypair.from_seed(bytes([211]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
BASE_MINT = Pubkey.from_bytes(bytes([15]) * 32)
OTHER = Pubkey.from_bytes(bytes([16]) * 32)
QUOTE_MINT = Pubkey.from_bytes(bytes([17]) * 32)
RESERVED = Pubkey.from_bytes(bytes([18]) * 32)
FEE_LIST = [Pubkey.from_bytes(bytes([40 + i]) * 32) for i in range(7)]  # sorted
RESERVED_LIST = [Pubkey.from_bytes(bytes([90 - i]) * 32) for i in range(7)]  # searched linearly


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


GLOBAL = pda(b'global')
CURVE = pda(b'bonding-curve', bytes(BASE_MINT))
VAULT = pda(b'creator-vault', bytes(CREATOR))
EVENT_AUTHORITY = pda(b'__event_authority')
RECIPIENTS = {'fee_recipient': FEE_RECIPIENT, 'fee_list': FEE_LIST[4], 'reserved': RESERVED,
              'reserved_list': RESERVED_LIST[5], 'vault': VAULT, 'other': OTHER, 'zero': SYSTEM}
TX_FEE = 5000
CURVE_RENT = 2_046_240  # Rent::minimum_balance(166)
TOKEN_RENT = 2_039_280
ZERO_RENT = 890_880
U64 = 2**64 - 1


def ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(decimals=6):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_data():
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    for i, key in enumerate(FEE_LIST):
        data[162 + 32 * i:194 + 32 * i] = bytes(key)
    data[483:515] = bytes(RESERVED)
    for i, key in enumerate(RESERVED_LIST):
        data[516 + 32 * i:548 + 32 * i] = bytes(key)
    return bytes(data)


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, item['real_quote'], 10**15)
    data[49:81] = bytes(CREATOR)
    data[81] = int(item['mayhem'])
    if not item['native']:
        data[83:115] = bytes(QUOTE_MINT)
    struct.pack_into('<QQ', data, 125, item['creator_fee'], item['protocol_fees'])
    return bytes(data)


DEFAULTS = dict(bucket='protocol', native=True, mayhem=False, real_quote=5 * 10**9, creator_fee=3_000_000,
                protocol_fees=7_000_000, curve_extra=CURVE_RENT, recipient='fee_recipient', recipient_lamports=10**9,
                curve_ata=10**10, recipient_ata=True, quote_mint=None, lamports=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['bucket'] == 'creator' and 'recipient' not in changes:
        item['recipient'] = 'vault'
    if item['quote_mint'] is None:
        item['quote_mint'] = 'native' if item['native'] else 'quote'
    return item


def curve_lamports(item):
    if item['lamports'] is not None:
        return item['lamports']
    reserved = item['real_quote'] + item['creator_fee'] + item['protocol_fees'] if item['native'] else 0
    return reserved + item['curve_extra']


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
    quote = {'native': NATIVE_MINT, 'quote': QUOTE_MINT, 'other': OTHER}[item['quote_mint']]
    recipient = RECIPIENTS[item['recipient']]
    accounts = {
        PAYER.pubkey(): Account(10**12, b'', SYSTEM),
        GLOBAL: Account(10**9, global_data(), PUMP),
        BASE_MINT: Account(10**9, mint_data(), TOKEN),
        NATIVE_MINT: Account(10**9, mint_data(9), TOKEN),
        QUOTE_MINT: Account(10**9, mint_data(), TOKEN),
        OTHER: Account(10**9, mint_data(), TOKEN),
        CURVE: Account(curve_lamports(item), curve_data(item), PUMP),
    }
    if item['recipient'] not in ('zero', 'other') and item['recipient_lamports']:
        accounts[recipient] = Account(item['recipient_lamports'], b'', SYSTEM)
    if not item['native']:
        if item['curve_ata'] is not None:
            accounts[ata(CURVE, QUOTE_MINT)] = Account(TOKEN_RENT, token_data(QUOTE_MINT, CURVE, item['curve_ata']), TOKEN)
        if item['recipient_ata']:
            accounts[ata(recipient, QUOTE_MINT)] = Account(TOKEN_RENT, token_data(QUOTE_MINT, recipient, 0), TOKEN)
    for key, account in accounts.items():
        vm.set_account(key, account)
    names = {
        'payer': PAYER.pubkey(), 'global': GLOBAL, 'base_mint': BASE_MINT, 'quote_mint': quote,
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'system_program': SYSTEM,
        'bonding_curve': CURVE, 'associated_quote_bonding_curve': ata(CURVE, quote), 'recipient': recipient,
        'associated_quote_recipient': ata(recipient, quote), 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX['sweep_creator_fee' if item['bucket'] == 'creator' else 'sweep_protocol_fee']
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    watched = (PAYER.pubkey(), CURVE, recipient)
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    delta = dict(zip(('payer', 'curve', 'recipient'), (lamports(k) - b for k, b in zip(watched, before))))
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    stored = vm.get_account(CURVE)
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0] if vm.get_account(key) else None
    return {'error': None, 'delta': delta, 'buckets': struct.unpack_from('<QQ', stored.data, 125) if stored else None,
            'events': [e for e in events if e[:8] == SWEEP_EVENT], 'all_events': len(events),
            'tokens': (tokens(ata(CURVE, quote)), tokens(ata(recipient, quote)))}


def recipient_lamports(item):
    return 0 if item['recipient'] in ('zero', 'other') else item['recipient_lamports']


def host_line(item):
    fields = [item['bucket'], int(item['native']), int(item['mayhem']), item['quote_mint'], item['real_quote'],
              item['creator_fee'], item['protocol_fees'], curve_lamports(item), item['recipient'],
              recipient_lamports(item), '-' if item['curve_ata'] is None else item['curve_ata'], int(item['recipient_ata'])]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    for native in (True, False):
        # Authorized recipients per bucket and mode.
        for recipient in ('fee_recipient', 'fee_list', 'reserved', 'reserved_list', 'vault', 'other', 'zero'):
            add(native=native, recipient=recipient)
            add(native=native, recipient=recipient, mayhem=True)
            add(native=native, recipient=recipient, bucket='creator')
        # Empty buckets: no transfer, no event, the other bucket untouched.
        add(native=native, protocol_fees=0)
        add(native=native, bucket='creator', creator_fee=0)
        add(native=native, protocol_fees=0, creator_fee=0, recipient='other')
        add(native=native, protocol_fees=1)
        add(native=native, protocol_fees=U64 // 4, creator_fee=U64 // 4, real_quote=0,
            curve_ata=U64 // 4)
        # Curve rent kept above what the curve owes, paid by the payer.
        for extra in (0, 1, CURVE_RENT - 1, CURVE_RENT, CURVE_RENT + 1, 10**9):
            add(native=native, curve_extra=extra or (0 if native else 1))
        add(native=native, protocol_fees=0, curve_extra=5)
        # Mint constraint.
        add(native=native, quote_mint='native' if not native else 'quote')
        add(native=native, quote_mint='other')
    # Native creator vault rent: the whole minimum when under it.
    for lamports in (0, 1, ZERO_RENT - 1, ZERO_RENT, 10**9):
        add(bucket='creator', recipient_lamports=lamports)
    add(bucket='creator', recipient_lamports=0, creator_fee=1)
    add(recipient_lamports=0, protocol_fees=ZERO_RENT - 1)
    # Native curve short of the SOL it owes.
    add(lamports=1_000)
    add(lamports=6_000_000)
    add(lamports=7_000_000 + CURVE_RENT - 1)
    # Boundaries after the payer's top-up: the curve holds exactly the amount
    # (accepted: the curve is drained to zero and dropped; one below overflows),
    # and the curve ends exactly at its rent minimum (accepted).
    for lamports in (7_000_000 - CURVE_RENT - 1, 7_000_000 - CURVE_RENT, 7_000_000 - CURVE_RENT + 1,
                     7_000_000 - 1, 7_000_000):
        add(lamports=lamports)
    add(lamports=10**12, real_quote=U64 - 5)
    add(lamports=10**12, real_quote=0, creator_fee=U64 - 5, protocol_fees=6)
    add(lamports=10**12, real_quote=0, creator_fee=U64 - 5, protocol_fees=5)
    # Quote curves: ATA existence and balance.
    add(native=False, curve_ata=None)
    add(native=False, curve_ata=None, protocol_fees=0)
    add(native=False, curve_ata=6_999_999)
    add(native=False, curve_ata=7_000_000)
    add(native=False, recipient_ata=False)
    add(native=False, recipient_ata=False, protocol_fees=0)
    add(native=False, recipient_ata=False, bucket='creator')
    add(native=False, recipient_ata=False, curve_ata=0)
    add(native=False, bucket='creator', recipient_lamports=0)
    add(native=False, real_quote=U64, protocol_fees=U64, curve_extra=1)
    return cases


def random_cases(count=80, seed=1443):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        native = rng.random() < 0.6
        bucket = rng.choice(('protocol', 'creator'))
        mayhem = rng.random() < 0.3
        valid = {'creator': ('vault',), 'protocol': ('reserved', 'reserved_list') if mayhem else ('fee_recipient', 'fee_list')}
        invalid = ('fee_recipient', 'fee_list', 'reserved', 'reserved_list', 'vault', 'other', 'zero')
        recipient = rng.choice(valid[bucket] if rng.random() < 0.8 else invalid)
        fee = lambda: rng.choice((0, rng.randrange(1, 10**6), rng.randrange(1, 10**11)))
        creator_fee, protocol_fees = fee(), fee()
        real_quote = rng.randrange(0, 10**11)
        reserved = real_quote + creator_fee + protocol_fees if native else 0
        lamports = reserved + rng.choice((0, rng.randrange(0, 3 * CURVE_RENT), rng.randrange(0, 10**10)))
        if rng.random() < 0.1:
            lamports = rng.randrange(1, max(reserved, 2))
        amount = creator_fee if bucket == 'creator' else protocol_fees
        cases.append(case(native=native, bucket=bucket, mayhem=mayhem, recipient=recipient, real_quote=real_quote,
                          creator_fee=creator_fee, protocol_fees=protocol_fees, lamports=max(lamports, 1),
                          recipient_lamports=rng.choice((0, rng.randrange(1, 2 * ZERO_RENT), 10**9)),
                          curve_ata=rng.choice((None, rng.randrange(0, amount + 2), 10**12)) if not native else 10**10,
                          recipient_ata=rng.random() < 0.6,
                          quote_mint=rng.choice((None,) * 9 + ('other',))))
    return cases


class SweepFeesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'sweep-fees-host'
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
        if answer == 'arithmetic':
            self.assertIn('ArithmeticOverflow', str(captured['error']))
            return
        if answer == 'rent':
            self.assertIn('InsufficientFundsForRent', str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        amount, curve_top_up, vault_top_up, ata_rent, creator_bucket, protocol_bucket = map(int, answer.split(',')[1:])
        native = item['native']
        self.assertEqual(captured['delta'], {
            'payer': -(curve_top_up + vault_top_up + ata_rent + TX_FEE),
            'curve': curve_top_up - (amount if native else 0),
            'recipient': vault_top_up + amount if native else 0,
        })
        # A native curve drained to exactly zero lamports is dropped by the runtime.
        drained = native and curve_lamports(item) + curve_top_up == amount
        self.assertEqual(captured['buckets'], None if drained else (creator_bucket, protocol_bucket))
        if not native:
            curve_ata, recipient_ata = captured['tokens']
            self.assertEqual(curve_ata, None if item['curve_ata'] is None else item['curve_ata'] - amount)
            created = item['recipient_ata'] or ata_rent
            self.assertEqual(recipient_ata, amount if created else None)
        if amount == 0:
            self.assertEqual((captured['events'], captured['all_events']), ([], 0))
            return
        recipient = RECIPIENTS[item['recipient']]
        quote = SYSTEM if native else QUOTE_MINT
        expected = (SWEEP_EVENT + struct.pack('<q', 1_700_000_000) + bytes(BASE_MINT) + bytes(CURVE) + bytes(quote)
                    + bytes(recipient) + struct.pack('<QB', amount, int(item['bucket'] == 'creator')))
        self.assertEqual(captured['events'], [expected])

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
        # Negative control: a passing captured creator sweep (vault top-up and
        # curve top-up included) must fail once any lamport movement is reversed.
        item = case(bucket='creator', recipient_lamports=0, curve_extra=0)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        for key in ('payer', 'curve', 'recipient'):
            with self.subTest(reversed=key):
                self.assertNotEqual(captured['delta'][key], 0)
                flipped = dict(captured, delta=dict(captured['delta'], **{key: -captured['delta'][key]}))
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'arithmetic', 'rent', 'error:1', 'error:2006', 'error:3012', 'error:6000', 'error:6004',
            'error:6024',
        })


if __name__ == '__main__':
    unittest.main()
