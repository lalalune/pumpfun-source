"""Captured-program checks for Pump creator-fee distribution on Token-2022 quotes.

Every case runs Pump `distribute_creator_fees_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs, against a synthetic quote curve,
SharingConfig and shareholder token accounts on a mint with Token-2022
extensions. The same inputs go to
`programs/pump/recovered/creator_fee_distribution_token2022_host.rs`, and the
error, token and lamport movements, withheld amounts, event, self-CPI copy and
return data must agree. This shows matching behavior on these inputs only; it
is not a byte-identity claim.
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
DEPS = ROOT / 'evidence/dependencies'
TOKEN_ELF = DEPS / 'spl_token/deployed.so'
TOKEN22_ELF = DEPS / 'spl_token_2022/deployed.so'
ATA_ELF = DEPS / 'associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_fee_distribution_token2022_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
EVENT_IX_TAG = bytes([228, 69, 165, 46, 81, 203, 154, 29])

PAYER = Keypair.from_seed(bytes([225]) * 32)
MINT = Pubkey.from_bytes(bytes([51]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([52]) * 32)
QUOTE = Pubkey.from_bytes(bytes([53]) * 32)
OTHER_QUOTE = Pubkey.from_bytes(bytes([54]) * 32)
ADMIN = Pubkey.from_bytes(bytes([55]) * 32)
OTHER = Pubkey.from_bytes(bytes([56]) * 32)
EXECUTABLE = Pubkey.from_bytes(bytes([57]) * 32)  # an unrelated captured program
HOLDERS = [Pubkey.from_bytes(bytes([70 + i]) * 32) for i in range(4)]
TX_FEE = 5000
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
FEE_250 = (0, 0, 0, 250, 10**18)


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(wallet, mint=QUOTE):
    return pda([bytes(wallet), bytes(TOKEN22), bytes(mint)], ATA)


CURVE = pda([b'bonding-curve', bytes(MINT)])
SHARING = pda([b'sharing-config', bytes(MINT)], FEES)
VAULT = pda([b'creator-vault', bytes(SHARING)])
EVENT_AUTHORITY = pda([b'__event_authority'])


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def plain_mint():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def quote_mint_data(item):
    ext = b''
    if item['fee']:
        older_bps, older_max, newer_epoch, newer_bps, newer_max = item['fee']
        ext += tlv(1, bytes(72) + struct.pack('<QQH', 0, older_max, older_bps)
                   + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    if item['hook_set']:
        ext += tlv(14, bytes(32) + bytes([7]) * 32)
    if item['paused']:
        ext += tlv(26, bytes(32) + b'\1')
    return plain_mint().ljust(165, b'\0') + bytes([1]) + ext if ext else plain_mint()


def token_data(mint, owner, amount, frozen=False, fee_extension=False, memo=False, cpi_guard=False, non_transferable=False):
    data = (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([2 if frozen else 1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))
    ext = b''
    if fee_extension:
        ext += tlv(2, bytes(8))
    if memo:
        ext += tlv(8, b'\1')
    if cpi_guard:
        ext += tlv(11, b'\1')
    if non_transferable:
        ext += tlv(13)
    return data + bytes([2]) + ext if ext else data


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 10**15, 3 * 10**10, 10**14, 10**9, 10**15)
    data[49:81] = bytes(SHARING if item['curve_creator'] == 'sharing' else OTHER)
    data[83:115] = bytes(QUOTE)
    struct.pack_into('<Q', data, 125, item['creator_fee'])
    return bytes(data)


def holder_address(i, h):
    return EXECUTABLE if h['wallet'] == 'exec' else HOLDERS[i]


def shareholders_bytes(item):
    return b''.join(bytes(holder_address(i, h)) + struct.pack('<H', h['bps']) for i, h in enumerate(item['holders']))


def sharing_data(item):
    return (ACCOUNT_DISC['SharingConfig'] + bytes([255, 1, int(item['active'])])
            + bytes(MINT if item['config_mint'] == 'mint' else OTHER_MINT) + bytes(ADMIN) + bytes([0])
            + struct.pack('<I', len(item['holders'])) + shareholders_bytes(item))


def holder(bps, wallet='ok', ata='exists', frozen=False, mint_mismatch=False, memo=False, no_fee_extension=False):
    return dict(bps=bps, wallet=wallet, ata=ata, frozen=frozen, mint_mismatch=mint_mismatch, memo=memo,
                no_fee_extension=no_fee_extension)


VAULT_FLAGS = ('frozen', 'owner_mismatch', 'mint_mismatch', 'cpi_guard', 'non_transferable')
DEFAULTS = dict(vault_tokens=10**9, holders=None, active=True, creator_fee=0, curve_creator='sharing', config_mint='mint',
                quote='quote', initialize_ata=False, vault={}, fee=None, epoch=0, hook_set=False, paused=False)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['holders'] is None:
        item['holders'] = [holder(5000), holder(3000), holder(2000)]
    return item


def host_line(item):
    fee = ':'.join(str(v) for v in item['fee']) if item['fee'] else '-'
    holders = ';'.join(f"{h['bps']}:{h['wallet']}:{h['ata']}:{int(h['frozen'])}:{int(h['mint_mismatch'])}:{int(h['memo'])}:"
                       f"{int(h['no_fee_extension'])}" for h in item['holders'])
    vault = ':'.join(str(int(item['vault'].get(name, False))) for name in VAULT_FLAGS)
    fields = ['-' if item['vault_tokens'] is None else item['vault_tokens'], int(item['active']), item['creator_fee'],
              int(item['curve_creator'] == 'sharing'), int(item['config_mint'] == 'mint'), int(item['quote'] == 'quote'),
              int(item['initialize_ata']), vault, fee, item['epoch'], int(item['hook_set']), int(item['paused']), holders]
    return ','.join(str(f) for f in fields)


def flat(data):
    return bytes(data[1:]) if data and isinstance(data[0], list) else bytes(data)


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    return 'invalid_account_data' if 'InvalidAccountData' in text else text


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
        for key, path in ((PUMP, PUMP_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF),
                          (EXECUTABLE, DEPS / 'donation_relay/deployed.so')):
            self.vm.add_program_from_file(key, path)
        self.stale = set()

    def run(self, item):
        vm = self.vm
        vm.set_clock(Clock(100, TIMESTAMP, item['epoch'], 0, TIMESTAMP))
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        fee_ext = bool(item['fee'])
        quote = QUOTE if item['quote'] == 'quote' else OTHER_QUOTE
        vault_ata = ata(VAULT, quote)
        accounts = {PAYER.pubkey(): Account(10**12, b'', SYSTEM), MINT: Account(10**9, plain_mint(), TOKEN),
                    QUOTE: Account(10**10, quote_mint_data(item), TOKEN22), OTHER_QUOTE: Account(10**10, quote_mint_data(item), TOKEN22),
                    CURVE: Account(10**9, curve_data(item), PUMP), SHARING: Account(10**9, sharing_data(item), FEES),
                    VAULT: Account(10**9, b'', SYSTEM), OTHER: Account(10**9, b'', SYSTEM),
                    ata(OTHER): Account(10**8, token_data(QUOTE, OTHER, 0, fee_extension=fee_ext), TOKEN22)}
        if item['vault_tokens'] is not None:
            v = item['vault']
            accounts[vault_ata] = Account(10**8, token_data(
                OTHER_QUOTE if v.get('mint_mismatch') and quote == QUOTE else quote, OTHER if v.get('owner_mismatch') else VAULT,
                item['vault_tokens'], frozen=v.get('frozen', False), fee_extension=fee_ext, cpi_guard=v.get('cpi_guard', False),
                non_transferable=v.get('non_transferable', False)), TOKEN22)
        wallets, atas, holder_atas = [], [], []
        for i, h in enumerate(item['holders']):
            address = holder_address(i, h)
            wallets.append(OTHER if h['wallet'] == 'wrong' else address)
            if h['wallet'] != 'exec':
                accounts[address] = Account(10**9, b'', SYSTEM)
            holder_atas.append(ata(address))
            atas.append(ata(OTHER) if h['ata'] == 'wrong' else ata(address))
            if h['ata'] == 'exists':
                accounts[ata(address)] = Account(10**8, token_data(
                    OTHER_QUOTE if h['mint_mismatch'] else QUOTE, address, 0, frozen=h['frozen'],
                    fee_extension=fee_ext and not h['no_fee_extension'], memo=h['memo']), TOKEN22)
        for key, account in accounts.items():
            vm.set_account(key, account)
        self.stale = {k for k in accounts if k != PAYER.pubkey()} | {vault_ata} | set(holder_atas)
        names = {'payer': PAYER.pubkey(), 'mint': MINT, 'bonding_curve': CURVE, 'sharing_config': SHARING,
                 'creator_vault': VAULT, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
                 'creator_vault_quote_token_account': vault_ata, 'quote_mint': quote, 'quote_token_program': TOKEN22,
                 'associated_token_program': ATA}
        ix = IX['distribute_creator_fees_v2']
        metas = [AccountMeta(names[a['name']], a['name'] == 'payer', a.get('writable', False)) for a in ix['accounts']]
        metas += [AccountMeta(key, False, True) for key in wallets + atas]

        def lamports(key):
            account = vm.get_account(key)
            return account.lamports if account else 0

        def raw(key):
            account = vm.get_account(key)
            return bytes(account.data) if account else b''

        def tokens(key):
            data = raw(key)
            return struct.unpack_from('<Q', data, 64)[0] if len(data) >= 72 else 0

        before = [lamports(k) for k in (PAYER.pubkey(), VAULT)]
        vault_before = tokens(vault_ata)
        data = bytes(ix['discriminator']) + bytes([int(item['initialize_ata'])])
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)],
                                               PAYER.pubkey(), [PAYER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return {'error': error_name(str(result.err()))}
        inner = [i for group in json.loads(result.to_json()).get('inner_instructions') or [] for i in group]
        return {'error': None, 'payer': lamports(PAYER.pubkey()) - before[0], 'vault': lamports(VAULT) - before[1],
                'vault_tokens': tokens(vault_ata) - vault_before, 'holder_tokens': [tokens(k) for k in holder_atas],
                'holder_withheld': [withheld(raw(k)) for k in holder_atas],
                'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')],
                'self_cpi': [d for d in (flat(i['instruction']['data']) for i in inner) if d.startswith(EVENT_IX_TAG)],
                'return_data': bytes(result.return_data().data)}


def event_payload(item, distributed):
    return (struct.pack('<q', TIMESTAMP) + bytes(MINT) + bytes(CURVE) + bytes(SHARING) + bytes(ADMIN)
            + struct.pack('<I', len(item['holders'])) + shareholders_bytes(item) + struct.pack('<Q', distributed)
            + bytes(QUOTE))


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    H = holder
    for fee in (None, FEE_250):
        add(fee=fee)
        for tokens in (None, 0, 1, 9_999, 10_000, 10**9 + 7, U64 // 10_000, U64 // 10_000 + 1):
            add(fee=fee, vault_tokens=tokens)
        add(fee=fee, vault_tokens=U64 // 5_000 + 1)
        add(fee=fee, vault_tokens=U64 // 5_000)
        add(fee=fee, curve_creator='other')
        add(fee=fee, config_mint='other')
        add(fee=fee, quote='other')
        add(fee=fee, active=False)
        add(fee=fee, creator_fee=1)
        add(fee=fee, creator_fee=1, vault_tokens=None)
        add(fee=fee, active=False, vault={'frozen': True})
        add(fee=fee, holders=[])
        add(fee=fee, holders=[], vault={'frozen': True})
        # Share checks run for all shareholders before any transfer failure.
        add(fee=fee, holders=[H(5000), H(5000, wallet='wrong')], vault={'frozen': True})
        add(fee=fee, holders=[H(5000), H(0)], vault={'frozen': True})
        add(fee=fee, holders=[H(5000), H(5000, ata='absent')], vault={'frozen': True})
        add(fee=fee, holders=[H(5000, frozen=True), H(5000, wallet='exec')])
        add(fee=fee, holders=[H(5000, memo=True), H(5000, ata='wrong')])
        add(fee=fee, holders=[H(5000), H(5000, wallet='exec', ata='absent')], initialize_ata=True)
        add(fee=fee, holders=[H(5000), H(5000, ata='absent')])
        add(fee=fee, holders=[H(5000), H(5000, ata='absent')], initialize_ata=True)
        add(fee=fee, holders=[H(5000, ata='absent'), H(3000, ata='absent'), H(2000, ata='absent')], initialize_ata=True)
        add(fee=fee, holders=[H(5000), H(5000)], initialize_ata=True)
        add(fee=fee, holders=[H(5000, ata='absent'), H(5000)], initialize_ata=True, vault={'frozen': True})
        add(fee=fee, holders=[H(5000, ata='absent')], initialize_ata=True, hook_set=True)
        # Over 10,000 bps: the failing transfer is the one past the balance.
        add(fee=fee, holders=[H(6000), H(6000)])
        add(fee=fee, holders=[H(6000), H(6000, frozen=True)])
        add(fee=fee, holders=[H(6000, frozen=True), H(6000)])
        add(fee=fee, holders=[H(6000), H(6000, memo=True)])
        add(fee=fee, holders=[H(6000), H(6000), H(1, frozen=True)])
        add(fee=fee, holders=[H(6000), H(6000)], paused=True)
        add(fee=fee, holders=[H(6000), H(6000)], vault={'non_transferable': True})
        add(fee=fee, holders=[H(5000), H(5000)], vault_tokens=1)
        add(fee=fee, holders=[H(10_000), H(1)], vault_tokens=10_000)
        add(fee=fee, holders=[H(10_000), H(1)], vault_tokens=9_999)
        # Zero-token shares never reach the transfer, whatever the accounts look like.
        add(fee=fee, holders=[H(1)], vault_tokens=9_999)
        add(fee=fee, holders=[H(1, frozen=True)], vault_tokens=9_999)
        add(fee=fee, holders=[H(1, memo=True)], vault_tokens=9_999)
        add(fee=fee, holders=[H(1, no_fee_extension=True)], vault_tokens=9_999)
        add(fee=fee, holders=[H(1, ata='absent')], vault_tokens=9_999, initialize_ata=True)
        add(fee=fee, holders=[H(1)], vault_tokens=9_999, paused=True)
        add(fee=fee, holders=[H(1)], vault_tokens=9_999, hook_set=True)
        add(fee=fee, holders=[H(1, ata='absent')], vault_tokens=9_999, initialize_ata=True, hook_set=True)
        add(fee=fee, holders=[H(1, ata='absent')], vault_tokens=9_999, initialize_ata=True, paused=True)
        add(fee=fee, holders=[H(1, ata='absent')], vault_tokens=9_999, initialize_ata=True, paused=True, hook_set=True)
        add(fee=fee, holders=[H(1)], vault_tokens=0, vault={'frozen': True})
        add(fee=fee, holders=[H(1)], vault_tokens=0, vault={'cpi_guard': True})
        # Which shareholder trips first.
        add(fee=fee, holders=[H(5000), H(3000, memo=True), H(2000, frozen=True)])
        add(fee=fee, holders=[H(5000), H(3000, frozen=True), H(2000, memo=True)])
        add(fee=fee, holders=[H(5000), H(3000, mint_mismatch=True), H(2000)])
    # Transfer fee: schedule choice, rounding, cap, whole amount.
    for fee, epoch in ((FEE_250, 0), ((0, 0, 0, 250, 100), 0), ((0, 0, 0, 10_000, 10**18), 0), ((100, 10**18, 5, 250, 10**18), 4),
                       ((100, 10**18, 5, 250, 10**18), 5), ((100, 10**18, 5, 250, 10**18), 6), ((100, 17, 5, 250, 10**18), 1),
                       ((0, 0, 0, 0, 10**18), 0), ((0, 0, 0, 250, 0), 0)):
        add(fee=fee, epoch=epoch)
        add(fee=fee, epoch=epoch, holders=[H(5000, ata='absent'), H(5000, no_fee_extension=True)], initialize_ata=True)
    for tokens in (1, 39, 40, 41, 79, 80, 81, 400, 401, 10_000, 20_001):
        add(fee=FEE_250, holders=[H(10_000)], vault_tokens=tokens)
        add(fee=FEE_250, holders=[H(5000), H(5000)], vault_tokens=tokens)
        add(fee=FEE_250, holders=[H(5000), H(5000, no_fee_extension=True)], vault_tokens=tokens)
    add(fee=(0, 0, 0, 10_000, U64), holders=[H(5000), H(5000)], vault_tokens=10**15)
    # Order of the token program's checks, pair by pair, on the first shareholder.
    faults = {
        'source_frozen': dict(vault=dict(frozen=True)), 'source_mint': dict(vault=dict(mint_mismatch=True)),
        'owner': dict(vault=dict(owner_mismatch=True)), 'non_transferable': dict(vault=dict(non_transferable=True)),
        'paused': dict(paused=True), 'cpi_guard': dict(vault=dict(cpi_guard=True)),
        'destination_frozen': dict(first=dict(frozen=True)), 'destination_mint': dict(first=dict(mint_mismatch=True)),
        'memo': dict(first=dict(memo=True)), 'no_fee_extension': dict(fee=FEE_250, first=dict(no_fee_extension=True)),
        'hook': dict(hook_set=True), 'short': dict(first=dict(bps=20_000)),
    }
    names = list(faults)
    for i, left in enumerate(names):
        cases.append(with_faults(faults[left]))
        for right in names[i + 1:]:
            cases.append(with_faults(faults[left], faults[right]))
    return cases


def with_faults(*faults):
    vault, first = {}, {}
    extra = {}
    for fault in faults:
        for key, value in fault.items():
            if key == 'vault':
                vault.update(value)
            elif key == 'first':
                first.update(value)
            else:
                extra[key] = value
    bps = first.pop('bps', 5000)
    return case(vault=vault, holders=[holder(bps, **first), holder(5000)], **extra)


def random_cases(count=300, seed=2210):
    rng = random.Random(seed)
    cases = []

    def fee():
        if rng.random() < 0.35:
            return None
        return (rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)), rng.randrange(0, 8),
                rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)))

    def held():
        flag = lambda p: rng.random() < p
        return holder(rng.choice((0, 1, 2_500, 5_000, 7_000, rng.randrange(1, 12_000))) if flag(0.9) else rng.randrange(1, 65_536),
                      wallet=rng.choice(('ok',) * 18 + ('wrong', 'exec')), ata=rng.choice(('exists',) * 6 + ('absent', 'absent', 'wrong')),
                      frozen=flag(0.05), mint_mismatch=flag(0.04), memo=flag(0.05), no_fee_extension=flag(0.08))

    for _ in range(count):
        vault = {name: True for name in VAULT_FLAGS if rng.random() < 0.05}
        cases.append(case(vault_tokens=rng.choice((None, 0, 1, rng.randrange(0, 10**5), rng.randrange(0, 10**12), rng.randrange(0, 10**15))),
                          holders=[held() for _ in range(rng.randrange(0, 5))], active=rng.random() > 0.03,
                          creator_fee=rng.choice((0,) * 19 + (1,)), initialize_ata=rng.random() < 0.7, vault=vault, fee=fee(),
                          epoch=rng.randrange(0, 8), hook_set=rng.random() < 0.06, paused=rng.random() < 0.06))
    return cases


class CreatorFeeDistributionToken2022CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-fee-distribution-token2022-host'
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
        if not answer.startswith('ok,'):
            self.assertEqual(captured['error'], answer)
            return
        self.assertIsNone(captured['error'])
        _, transfers, kept, distributed, ata_rent = answer.split(',')
        transfers = [int(v) for v in transfers.split(';') if v]
        kept = [int(v) for v in kept.split(';') if v]
        distributed = int(distributed)
        self.assertEqual(captured['payer'], -(TX_FEE + int(ata_rent)))
        self.assertEqual(captured['vault'], 0)
        self.assertEqual(captured['vault_tokens'], -distributed)
        self.assertEqual(captured['holder_tokens'], [t - k for t, k in zip(transfers, kept)])
        self.assertEqual(captured['holder_withheld'], kept)
        payload = event_payload(item, distributed)
        event = EVENT_DISC['DistributeCreatorFeesEvent'] + payload
        self.assertEqual(captured['events'], [event])
        self.assertEqual(captured['self_cpi'], [EVENT_IX_TAG + event])
        self.assertEqual(captured['return_data'], payload)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.chain.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_wrong_withheld_amount(self):
        item = case(fee=FEE_250)
        answer = self.host_answers([item])[0]
        captured = self.chain.run(item)
        self.assert_matches(item, answer, captured)
        for broken in (dict(captured, holder_withheld=[v + 1 for v in captured['holder_withheld']]),
                       dict(captured, vault_tokens=-captured['vault_tokens'])):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, broken)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'invalid_account_data', 'error:1', 'error:3', 'error:4', 'error:13', 'error:17', 'error:36', 'error:37',
            'error:42', 'error:67', 'error:6004', 'error:6024', 'error:6051', 'error:6052', 'error:6053', 'error:6054',
            'error:6055', 'error:6070', 'error:6095',
        })


if __name__ == '__main__':
    unittest.main()
