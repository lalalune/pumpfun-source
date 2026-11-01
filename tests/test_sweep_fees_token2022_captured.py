"""Captured-program checks for the Pump fee sweep on Token-2022 quote mints.

Every case runs Pump `sweep_protocol_fee` or `sweep_creator_fee` from the
captured `evidence/original/pump/deployed.so` on LiteSVM, with the captured
SPL Token, Token-2022 and Associated Token programs, against a synthetic quote
curve whose mint carries Token-2022 extensions. The same inputs go to
`programs/pump/recovered/sweep_fees_token2022_host.rs`, and the error, lamport
and token movements, withheld amounts, the created ATA, stored fee buckets, and
SweepBondingCurveFeeEvent must agree. This shows matching behavior on these
inputs only; it is not a byte-identity claim.
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
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/sweep_fees_token2022_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
SWEEP_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'SweepBondingCurveFeeEvent'))

PAYER = Keypair.from_seed(bytes([212]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
BASE_MINT = Pubkey.from_bytes(bytes([15]) * 32)
OTHER = Pubkey.from_bytes(bytes([16]) * 32)
QUOTE_MINT = Pubkey.from_bytes(bytes([17]) * 32)
RESERVED = Pubkey.from_bytes(bytes([18]) * 32)
WRONG_ATA = Pubkey.from_bytes(bytes([19]) * 32)
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
PROGRAMS = {'t22': TOKEN22, 'spl': TOKEN, 'other': OTHER}
TX_FEE = 5000
CURVE_RENT = 2_046_240  # Rent::minimum_balance(166)
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
FEE_250 = (0, 0, 0, 250, 10**18)


def ata(owner, mint, program):
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA)[0]


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint_data(item):
    base = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)
    ext = b''
    if item['fee']:
        older_bps, older_max, newer_epoch, newer_bps, newer_max = item['fee']
        ext += tlv(1, bytes(72) + struct.pack('<QQH', 0, older_max, older_bps)
                   + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    if item['hook'] != 'none':
        ext += tlv(14, bytes(32) + (bytes(32) if item['hook'] == 'unset' else bytes([7]) * 32))
    if item['pausable'] != 'none':
        ext += tlv(26, bytes(32) + bytes([item['pausable'] == 'paused']))
    if item['non_transferable']:
        ext += tlv(9)
    if item['default_frozen']:
        ext += tlv(6, bytes([2]))
    return base.ljust(165, b'\0') + bytes([1]) + ext if ext else base


HOLDING = dict(balance=10**10, frozen=False, fee_extension=None, owner_matches=True, memo=False, cpi_guard=False,
               non_transferable=False)


def holding(**changes):
    return dict(HOLDING, **changes)


def token_data(holder, owner, fallback_fee_extension):
    mint = OTHER if holder == 'wrong_mint' else QUOTE_MINT
    held = HOLDING if isinstance(holder, str) else holder
    fee_extension = fallback_fee_extension if held['fee_extension'] is None else held['fee_extension']
    data = (bytes(mint) + bytes(owner if held['owner_matches'] else OTHER) + struct.pack('<Q', held['balance'])
            + struct.pack('<I', 0) + bytes(32) + bytes([0 if holder == 'uninitialized' else 2 if held['frozen'] else 1])
            + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))
    ext = b''
    if fee_extension:
        ext += tlv(2, bytes(8))
    if held['memo']:
        ext += tlv(8, b'\1')
    if held['cpi_guard']:
        ext += tlv(11, b'\1')
    if held['non_transferable']:
        ext += tlv(13)
    data = data + bytes([2]) + ext if ext else data
    return data[:100] if holder == 'truncated' else data


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
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, 5 * 10**9, 10**15)
    data[49:81] = bytes(CREATOR)
    data[81] = int(item['mayhem'])
    data[83:115] = bytes(QUOTE_MINT)
    struct.pack_into('<QQ', data, 125, item['creator_fee'], item['protocol_fees'])
    return bytes(data)


DEFAULTS = dict(bucket='protocol', mayhem=False, quote_mint='quote', creator_fee=3_000_000, protocol_fees=7_000_000,
                curve_lamports=CURVE_RENT, recipient='fee_recipient', recipient_lamports=10**9, token_program='t22',
                mint_owner='t22', fee=None, epoch=0, hook='none', pausable='none', non_transferable=False,
                default_frozen=False, curve_address_ok=True, recipient_address_ok=True, curve_ata=None,
                recipient_ata=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['bucket'] == 'creator' and 'recipient' not in changes:
        item['recipient'] = 'vault'
    if item['curve_ata'] is None:
        item['curve_ata'] = holding()
    if item['recipient_ata'] is None:
        item['recipient_ata'] = holding(balance=0)
    return item


def has_fee_extension(item, held):
    if isinstance(held, str) or held['fee_extension'] is None:
        return bool(item['fee'])
    return held['fee_extension']


def host_ata(item, held):
    if isinstance(held, str):
        return held
    return ':'.join(str(int(v)) for v in (held['balance'], held['frozen'], has_fee_extension(item, held),
                                          held['owner_matches'], held['memo'], held['cpi_guard'], held['non_transferable']))


def recipient_lamports(item):
    return 0 if item['recipient'] in ('zero', 'other') else item['recipient_lamports']


def host_line(item):
    fee = ':'.join(str(v) for v in item['fee']) if item['fee'] else '-'
    fields = [item['bucket'], int(item['mayhem']), item['quote_mint'], item['creator_fee'], item['protocol_fees'],
              item['curve_lamports'], item['recipient'], recipient_lamports(item), item['token_program'],
              item['mint_owner'], fee, item['epoch'], item['hook'], item['pausable'], int(item['non_transferable']),
              int(item['default_frozen']), int(item['curve_address_ok']), int(item['recipient_address_ok']),
              host_ata(item, item['curve_ata']), host_ata(item, item['recipient_ata'])]
    return ','.join(str(f) for f in fields)


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name in ('InvalidAccountData', 'UninitializedAccount', 'IncorrectProgramId'):
        if name in text:
            return re.sub(r'(?<!^)([A-Z])', r'_\1', name).lower()
    return text


def withheld(data):
    offset = 166
    while offset + 4 <= len(data):
        kind, length = struct.unpack_from('<HH', data, offset)
        if kind == 2:
            return struct.unpack_from('<Q', data, offset + 4)[0]
        if kind == 0:
            break
        offset += 4 + length
    return 0


class Chain:
    """One VM for every case: reloading the ELFs costs far more than a transaction."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((PUMP, PUMP_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF)):
            self.vm.add_program_from_file(key, path)
        self.stale = set()

    def run(self, item):
        vm = self.vm
        vm.set_clock(Clock(100, TIMESTAMP, item['epoch'], 0, TIMESTAMP))
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        program = PROGRAMS[item['token_program']]
        quote = OTHER if item['quote_mint'] == 'other' else QUOTE_MINT
        recipient = RECIPIENTS[item['recipient']]
        curve_ata, recipient_ata = ata(CURVE, quote, program), ata(recipient, quote, program)
        owner = {'t22': TOKEN22, 'spl': TOKEN, 'other': SYSTEM}[item['mint_owner']]
        accounts = {
            PAYER.pubkey(): Account(10**12, b'', SYSTEM),
            GLOBAL: Account(10**9, global_data(), PUMP),
            BASE_MINT: Account(10**9, mint_data(DEFAULTS), TOKEN),
            quote: Account(10**10, mint_data(item), owner),
            CURVE: Account(item['curve_lamports'], curve_data(item), PUMP),
        }
        if recipient_lamports(item):
            accounts[recipient] = Account(item['recipient_lamports'], b'', SYSTEM)
        token_owner = program if program != OTHER else TOKEN22
        ata_lamports = 10**8
        for key, holder, authority in ((curve_ata, item['curve_ata'], CURVE), (recipient_ata, item['recipient_ata'], recipient)):
            if holder == 'missing':
                continue
            account_owner = (TOKEN if token_owner == TOKEN22 else TOKEN22) if holder == 'wrong_program' else token_owner
            accounts[key] = Account(ata_lamports, token_data(holder, authority, bool(item['fee'])), account_owner)
        for key, account in accounts.items():
            vm.set_account(key, account)
        passed_curve_ata = curve_ata if item['curve_address_ok'] else WRONG_ATA
        passed_recipient_ata = recipient_ata if item['recipient_address_ok'] else WRONG_ATA
        self.stale = set(accounts) | {curve_ata, recipient_ata}
        names = {
            'payer': PAYER.pubkey(), 'global': GLOBAL, 'base_mint': BASE_MINT, 'quote_mint': quote,
            'quote_token_program': program, 'associated_token_program': ATA, 'system_program': SYSTEM,
            'bonding_curve': CURVE, 'associated_quote_bonding_curve': passed_curve_ata, 'recipient': recipient,
            'associated_quote_recipient': passed_recipient_ata, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
        }
        ix = IX['sweep_creator_fee' if item['bucket'] == 'creator' else 'sweep_protocol_fee']
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]

        def lamports(key):
            account = vm.get_account(key)
            return account.lamports if account else 0

        def data(key):
            account = vm.get_account(key)
            return bytes(account.data) if account else b''

        watched = (PAYER.pubkey(), CURVE, recipient, curve_ata, recipient_ata)
        before = [lamports(key) for key in watched]
        recipient_before = data(recipient_ata)
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                               [PAYER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return {'error': error_name(str(result.err()))}
        delta = [lamports(key) - b for key, b in zip(watched, before)]
        events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
        curve_tokens, recipient_tokens = data(curve_ata), data(recipient_ata)
        tokens = lambda raw: struct.unpack_from('<Q', raw, 64)[0] if len(raw) >= 72 else None
        return {'error': None, 'delta': delta, 'buckets': struct.unpack_from('<QQ', data(CURVE), 125),
                'events': [e for e in events if e[:8] == SWEEP_EVENT], 'all_events': len(events),
                'curve_tokens': tokens(curve_tokens), 'recipient_tokens': tokens(recipient_tokens),
                'recipient_withheld': withheld(recipient_tokens), 'recipient_len': len(recipient_tokens),
                'recipient_before': tokens(recipient_before)}


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    fees = (None, FEE_250)
    for fee in fees:
        # Authorized recipients per bucket and mode, as on an SPL quote.
        for recipient in ('fee_recipient', 'fee_list', 'reserved', 'reserved_list', 'vault', 'other', 'zero'):
            add(fee=fee, recipient=recipient)
            add(fee=fee, recipient=recipient, mayhem=True)
            add(fee=fee, recipient=recipient, bucket='creator')
        # Empty buckets end before any ATA is looked at.
        add(fee=fee, protocol_fees=0)
        add(fee=fee, protocol_fees=0, curve_ata='missing', recipient_ata='missing')
        add(fee=fee, protocol_fees=0, curve_ata='wrong_program', recipient_ata='truncated')
        add(fee=fee, bucket='creator', creator_fee=0, curve_ata='wrong_mint')
        # Curve rent, paid by the payer before anything else.
        for lamports in (1, CURVE_RENT - 1, CURVE_RENT, CURVE_RENT + 1):
            add(fee=fee, curve_lamports=lamports)
        add(fee=fee, curve_lamports=1, protocol_fees=0)
        # Curve and recipient ATA admission.
        for holder in ('missing', 'wrong_program', 'truncated', 'uninitialized', 'wrong_mint'):
            add(fee=fee, curve_ata=holder)
            add(fee=fee, recipient_ata=holder)
            add(fee=fee, curve_ata=holder, recipient='other')
            add(fee=fee, curve_ata=holder, recipient_ata='wrong_program')
            add(fee=fee, curve_ata=holder, recipient_ata='missing')
            add(fee=fee, curve_ata=holder, curve_address_ok=False)
        add(fee=fee, curve_address_ok=False)
        add(fee=fee, recipient_address_ok=False)
        add(fee=fee, recipient_address_ok=False, recipient='other')
        add(fee=fee, curve_address_ok=False, recipient='other', protocol_fees=0)
        add(fee=fee, curve_address_ok=False, quote_mint='other')
        add(fee=fee, quote_mint='other')
        add(fee=fee, mint_owner='other')
        add(fee=fee, mint_owner='other', quote_mint='other')
        add(fee=fee, token_program='other')
        add(fee=fee, token_program='other', mint_owner='other')
        add(fee=fee, token_program='other', quote_mint='other')
        # Program and mint owner mixes.
        add(fee=fee, mint_owner='spl')
        add(fee=fee, mint_owner='spl', curve_ata=holding(frozen=True))
        add(fee=fee, mint_owner='spl', curve_ata=holding(balance=1))
        add(fee=fee, mint_owner='spl', curve_ata=holding(owner_matches=False))
        add(fee=fee, mint_owner='spl', recipient_ata=holding(balance=0, frozen=True))
        add(fee=fee, mint_owner='spl', recipient_ata='missing')
        add(fee=fee, mint_owner='spl', recipient_ata='missing', curve_ata=holding(balance=1))
        add(fee=fee, mint_owner='spl', recipient_ata='missing', curve_ata=holding(frozen=True))
        add(fee=fee, token_program='spl')
        add(fee=fee, token_program='spl', curve_ata=holding(frozen=True, fee_extension=False))
        add(fee=fee, token_program='spl', curve_ata=holding(balance=1, fee_extension=False))
        add(fee=fee, token_program='spl', curve_ata=holding(fee_extension=False))
    # Transfer fee: schedule choice, rounding, cap, whole amount.
    for fee, epoch in ((FEE_250, 0), ((0, 0, 0, 250, 100), 0), ((0, 0, 0, 10_000, 10**18), 0), ((100, 10**18, 5, 250, 10**18), 0),
                       ((100, 10**18, 5, 250, 10**18), 4), ((100, 10**18, 5, 250, 10**18), 5), ((100, 10**18, 5, 250, 10**18), 6),
                       ((100, 17, 5, 250, 10**18), 1), ((0, 0, 0, 0, 10**18), 0), ((0, 0, 0, 250, 0), 0)):
        add(fee=fee, epoch=epoch)
        add(fee=fee, epoch=epoch, bucket='creator')
        add(fee=fee, epoch=epoch, recipient_ata='missing')
    for amount in (1, 39, 40, 41, 79, 80, 81, 400, 401):
        add(fee=FEE_250, protocol_fees=amount)
        add(fee=FEE_250, protocol_fees=amount, recipient_ata=holding(balance=0, fee_extension=False))
    add(fee=(0, 0, 0, 10_000, U64), protocol_fees=U64, curve_ata=holding(balance=U64))
    add(fee=(0, 0, 0, 9_999, U64), protocol_fees=U64, curve_ata=holding(balance=U64))
    add(fee=FEE_250, protocol_fees=U64 - 1, curve_ata=holding(balance=U64 - 1))
    # A destination without the fee account extension only matters with a non-zero fee.
    add(fee=(0, 0, 0, 0, 10**18), recipient_ata=holding(balance=0, fee_extension=False))
    add(fee=(0, 0, 0, 250, 0), recipient_ata=holding(balance=0, fee_extension=False))
    add(fee=FEE_250, recipient_ata=holding(balance=0, fee_extension=False))
    add(fee=FEE_250, curve_ata=holding(fee_extension=False))
    # The created ATA size follows the mint.
    for fee in fees:
        for hook in ('none', 'unset', 'set'):
            for pausable in ('none', 'running', 'paused'):
                for non_transferable in (False, True):
                    add(fee=fee, hook=hook, pausable=pausable, non_transferable=non_transferable, recipient_ata='missing')
                    add(fee=fee, hook=hook, pausable=pausable, non_transferable=non_transferable)
        add(fee=fee, default_frozen=True, recipient_ata='missing')
        add(fee=fee, default_frozen=True)
        add(fee=fee, default_frozen=True, recipient_ata='missing', curve_ata=holding(balance=1))
        add(fee=fee, recipient_ata='missing', bucket='creator', recipient='vault', recipient_lamports=0)
    # Order of the token program's checks, pair by pair.
    faults = {
        'source_frozen': dict(curve_ata=dict(frozen=True)), 'short': dict(curve_ata=dict(balance=1)),
        'mint_owner': dict(mint_owner='spl'), 'owner': dict(curve_ata=dict(owner_matches=False)), 'non_transferable': dict(curve_ata=dict(non_transferable=True)),
        'paused': dict(pausable='paused'), 'cpi_guard': dict(curve_ata=dict(cpi_guard=True)),
        'destination_frozen': dict(recipient_ata=dict(frozen=True)), 'memo': dict(recipient_ata=dict(memo=True)),
        'no_fee_extension': dict(fee=FEE_250, recipient_ata=dict(fee_extension=False)), 'hook': dict(hook='set'),
    }
    names = list(faults)
    for i, left in enumerate(names):
        cases.append(with_faults(faults[left]))
        for right in names[i + 1:]:
            cases.append(with_faults(faults[left], faults[right]))
    return cases


def with_faults(*faults):
    merged = dict(curve_ata={}, recipient_ata=dict(balance=0))
    extra = {}
    for fault in faults:
        for key, value in fault.items():
            if key in merged:
                merged[key] = dict(merged[key], **value)
            else:
                extra[key] = value
    return case(curve_ata=holding(**merged['curve_ata']), recipient_ata=holding(**merged['recipient_ata']), **extra)


def random_cases(count=400, seed=2207):
    rng = random.Random(seed)
    cases = []
    amount = lambda: rng.choice((0, 1, rng.randrange(1, 10**4), rng.randrange(1, 10**7), rng.randrange(1, 10**12)))

    def fee():
        if rng.random() < 0.4:
            return None
        return (rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)), rng.randrange(0, 8),
                rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)))

    def held(source):
        roll = rng.random()
        if roll < 0.05:
            return rng.choice(('missing', 'wrong_program', 'truncated', 'uninitialized', 'wrong_mint'))
        flag = lambda p: rng.random() < p
        return holding(balance=rng.choice((0, rng.randrange(0, 10**7), 10**13)) if source else rng.randrange(0, 10**6),
                       frozen=flag(0.08), fee_extension=None if flag(0.9) else flag(0.5), owner_matches=not (source and flag(0.05)),
                       memo=flag(0.08), cpi_guard=flag(0.08), non_transferable=flag(0.08))

    for _ in range(count):
        bucket = rng.choice(('protocol', 'creator'))
        mayhem = rng.random() < 0.3
        valid = {'creator': ('vault',), 'protocol': ('reserved', 'reserved_list') if mayhem else ('fee_recipient', 'fee_list')}
        invalid = ('fee_recipient', 'fee_list', 'reserved', 'reserved_list', 'vault', 'other', 'zero')
        recipient = rng.choice(valid[bucket] if rng.random() < 0.9 else invalid)
        cases.append(case(
            bucket=bucket, mayhem=mayhem, recipient=recipient, creator_fee=amount(), protocol_fees=amount(),
            curve_lamports=rng.choice((CURVE_RENT, rng.randrange(1, 2 * CURVE_RENT), 10**10)),
            recipient_lamports=rng.choice((0, rng.randrange(1, 10**7), 10**9)),
            fee=fee(), epoch=rng.randrange(0, 8), hook=rng.choice(('none', 'none', 'none', 'unset', 'set')),
            pausable=rng.choice(('none', 'none', 'running', 'paused')), non_transferable=rng.random() < 0.1,
            default_frozen=rng.random() < 0.1, curve_ata=held(True),
            recipient_ata=rng.choice(('missing', held(False), held(False))),
            quote_mint=rng.choice(('quote',) * 19 + ('other',)), curve_address_ok=rng.random() > 0.03,
            recipient_address_ok=rng.random() > 0.03, mint_owner=rng.choice(('t22',) * 18 + ('spl', 'other')),
            token_program=rng.choice(('t22',) * 19 + ('other',))))
    return cases


class SweepFeesToken2022CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'sweep-fees-token2022-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.chain = Chain()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer != 'ok' and not answer.startswith('ok,'):
            self.assertEqual(captured['error'], answer)
            return
        self.assertIsNone(captured['error'])
        amount, kept, top_up, ata_rent, ata_len, creator_bucket, protocol_bucket = map(int, answer.split(',')[1:])
        self.assertEqual(captured['delta'][:3], [-(top_up + ata_rent + TX_FEE), top_up, 0])
        self.assertEqual(captured['buckets'], (creator_bucket, protocol_bucket))
        if amount == 0:
            self.assertEqual((captured['events'], captured['all_events']), ([], 0))
            return
        self.assertEqual(captured['delta'][3], 0)
        self.assertEqual(captured['delta'][4], ata_rent)
        self.assertEqual(captured['curve_tokens'], item['curve_ata']['balance'] - amount)
        start = 0 if item['recipient_ata'] == 'missing' else item['recipient_ata']['balance']
        self.assertEqual(captured['recipient_tokens'], start + amount - kept)
        self.assertEqual(captured['recipient_withheld'], kept)
        if ata_len:
            self.assertEqual(captured['recipient_len'], ata_len)
        recipient = RECIPIENTS[item['recipient']]
        expected = (SWEEP_EVENT + struct.pack('<q', TIMESTAMP) + bytes(BASE_MINT) + bytes(CURVE) + bytes(QUOTE_MINT)
                    + bytes(recipient) + struct.pack('<QB', amount, int(item['bucket'] == 'creator')))
        self.assertEqual(captured['events'], [expected])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.chain.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_an_unknown_column_token_is_refused(self):
        # The parser's catchalls read any other token as a real value, so a
        # misspelt or shifted column silently selected a different case.
        malformed = dict(bucket='creatorr', quote_mint='quoted', token_program='t222', mint_owner='spll',
                         hook='sett', pausable='pausedd')
        for column, value in malformed.items():
            with self.subTest(column=column):
                text = host_line(case(**{column: value})) + '\n'
                run = subprocess.run([str(self.host)], input=text, capture_output=True, text=True)
                self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_wrong_withheld_amount(self):
        # Negative control: a passing captured sweep must fail once the
        # withheld amount or a lamport movement is altered.
        item = case(fee=FEE_250, recipient_ata='missing')
        answer = self.host_answers([item])[0]
        captured = self.chain.run(item)
        self.assert_matches(item, answer, captured)
        for broken in (dict(captured, recipient_withheld=captured['recipient_withheld'] + 1),
                       dict(captured, recipient_tokens=captured['recipient_tokens'] + 1),
                       dict(captured, delta=[-v for v in captured['delta']])):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, broken)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'invalid_account_data', 'uninitialized_account', 'incorrect_program_id', 'error:1', 'error:4',
            'error:13', 'error:17', 'error:36', 'error:37', 'error:42', 'error:67', 'error:2006', 'error:3007',
            'error:3008', 'error:3012', 'error:6000', 'error:6004', 'error:6010',
        })


if __name__ == '__main__':
    unittest.main()
