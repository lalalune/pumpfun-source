"""Captured-program checks for Pump `claim_cashback_v2` on Token-2022 quotes.

Every case runs the token route of `claim_cashback_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs, against a synthetic
UserVolumeAccumulator and a mint with Token-2022 extensions. The same inputs go
to `programs/pump/recovered/claim_cashback_v2_token2022_host.rs`, and the
error, token movements, withheld amount, stored UVA bytes and ClaimCashbackEvent
must agree. This shows matching behavior on these inputs only; it is not a
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
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/claim_cashback_v2_token2022_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
UVA_DISC = bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name'] == 'UserVolumeAccumulator'))
IX = next(i for i in IDL['instructions'] if i['name'] == 'claim_cashback_v2')

PAYER = Keypair.from_seed(bytes([224]) * 32)
USER = Pubkey.from_bytes(bytes([28]) * 32)
QUOTE_MINT = Pubkey.from_bytes(bytes([29]) * 32)
STRANGER = Pubkey.from_bytes(bytes([30]) * 32)
WRONG_ATA = Pubkey.from_bytes(bytes([31]) * 32)
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
UVA_LEN = 137
FEE_250 = (0, 0, 0, 250, 10**18)
PROGRAMS = {'t22': TOKEN22, 'spl': TOKEN, 'system': SYSTEM}


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


EVENT_AUTHORITY = pda(b'__event_authority')
UVA = pda(b'user_volume_accumulator', bytes(USER))


def ata(owner, mint, program):
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA)[0]


def rent(size):
    return (128 + size) * 6960


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint_data(item):
    base = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)
    if item['mint_truncated']:
        return base[:40]
    ext = b''
    if item['fee']:
        older_bps, older_max, newer_epoch, newer_bps, newer_max = item['fee']
        ext += tlv(1, bytes(72) + struct.pack('<QQH', 0, older_max, older_bps)
                   + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    if item['hook_set']:
        ext += tlv(14, bytes(32) + bytes([7]) * 32)
    if item['paused']:
        ext += tlv(26, bytes(32) + b'\1')
    return base.ljust(165, b'\0') + bytes([1]) + ext if ext else base


HOLDING = dict(balance=500_000, frozen=False, fee_extension=None, owner_matches=True, mint_matches=True, memo=False,
               cpi_guard=False, non_transferable=False, wrong_program=False)


def holding(**changes):
    return dict(HOLDING, **changes)


def token_data(holder, owner, fallback_fee_extension):
    held = HOLDING if isinstance(holder, str) else holder
    fee_extension = fallback_fee_extension if held['fee_extension'] is None else held['fee_extension']
    data = (bytes(QUOTE_MINT if held['mint_matches'] else STRANGER) + bytes(owner if held['owner_matches'] else STRANGER)
            + struct.pack('<Q', held['balance']) + struct.pack('<I', 0) + bytes(32)
            + bytes([0 if holder == 'uninitialized' else 2 if held['frozen'] else 1])
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


DEFAULTS = dict(extra=1_000_000, claimed=7_000, stable_claimed=8_000, earned=9_000_000, stable_earned=10_000_000,
                token_program='t22', mint_owner='t22', mint_truncated=False, fee=None, epoch=0, hook_set=False, paused=False,
                address_ok=True, uva_ata=None, user_ata=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['uva_ata'] is None:
        item['uva_ata'] = holding()
    if item['user_ata'] is None:
        item['user_ata'] = holding(balance=3)
    return item


def uva_data(item):
    data = bytearray((i * 37 + 11) % 256 for i in range(UVA_LEN))
    head = UVA_DISC + bytes(USER) + bytes([1]) + struct.pack('<QQQq', 5, 6, 7, TIMESTAMP - 50) + bytes([1])
    head += struct.pack('<QQQQ', item['earned'], item['claimed'], item['stable_earned'], item['stable_claimed'])
    data[:len(head)] = head
    return bytes(data)


def host_ata(item, held):
    if isinstance(held, str):
        return held
    fee_extension = bool(item['fee']) if held['fee_extension'] is None else held['fee_extension']
    text = ':'.join(str(int(v)) for v in (held['balance'], held['frozen'], fee_extension, held['owner_matches'],
                                          held['mint_matches'], held['memo'], held['cpi_guard'], held['non_transferable']))
    return 'wrong:' + text if held['wrong_program'] else text


def host_line(item):
    fee = ':'.join(str(v) for v in item['fee']) if item['fee'] else '-'
    fields = [bytes(USER).hex(), int(item['token_program'] != 'system'), int(item['mint_owner'] == item['token_program']),
              int(item['mint_truncated']), fee, int(item['hook_set']), int(item['paused']), item['epoch'],
              int(item['address_ok']), host_ata(item, item['uva_ata']), host_ata(item, item['user_ata']),
              rent(UVA_LEN) + item['extra'], uva_data(item).hex(), TIMESTAMP]
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
        token_owner = TOKEN if program == TOKEN else TOKEN22
        mint_owner = {'t22': TOKEN22, 'spl': TOKEN, 'system': SYSTEM}[item['mint_owner']]
        uva_ata, user_ata = ata(UVA, QUOTE_MINT, program), ata(USER, QUOTE_MINT, token_owner)
        accounts = {PAYER.pubkey(): Account(10**12, b'', SYSTEM), USER: Account(10**9, b'', SYSTEM),
                    UVA: Account(rent(UVA_LEN) + item['extra'], uva_data(item), PUMP),
                    QUOTE_MINT: Account(10**10, mint_data(item), mint_owner)}
        for key, holder, authority in ((uva_ata, item['uva_ata'], UVA), (user_ata, item['user_ata'], USER)):
            if holder == 'missing':
                continue
            wrong = not isinstance(holder, str) and holder['wrong_program']
            accounts[key] = Account(10**8, token_data(holder, authority, bool(item['fee'])),
                                    (TOKEN if token_owner == TOKEN22 else TOKEN22) if wrong else token_owner)
        for key, account in accounts.items():
            vm.set_account(key, account)
        self.stale = {k for k in accounts if k != PAYER.pubkey()} | {uva_ata, user_ata}
        named = {'user': USER, 'user_volume_accumulator': UVA, 'quote_mint': QUOTE_MINT, 'quote_token_program': program,
                 'associated_token_program': ATA, 'associated_user_volume_accumulator': uva_ata if item['address_ok'] else WRONG_ATA,
                 'associated_quote_user': user_ata, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY,
                 'program': PUMP}
        metas = [AccountMeta(named[a['name']], False, a.get('writable', False)) for a in IX['accounts']]

        def data(key):
            account = vm.get_account(key)
            return bytes(account.data) if account else b''

        def tokens(key):
            raw = data(key)
            return struct.unpack_from('<Q', raw, 64)[0] if len(raw) >= 72 else 0

        lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
        before = (lamports(USER), lamports(UVA), tokens(uva_ata), tokens(user_ata))
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(IX['discriminator']), metas)], PAYER.pubkey(),
                                               [PAYER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            if any('panicked' in line for line in result.meta().logs()):
                return {'error': 'panic'}
            return {'error': error_name(str(result.err()))}
        return {'error': None, 'lamports': (lamports(USER) - before[0], lamports(UVA) - before[1]),
                'uva_tokens': tokens(uva_ata) - before[2], 'user_tokens': tokens(user_ata) - before[3],
                'withheld': withheld(data(user_ata)), 'uva': data(UVA),
                'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def with_faults(*faults):
    merged = dict(uva_ata={}, user_ata=dict(balance=3))
    extra = {}
    for fault in faults:
        for key, value in fault.items():
            if key in merged and isinstance(value, dict):
                merged[key] = dict(merged[key], **value)
            else:
                extra[key] = value
    args = dict(uva_ata=holding(**merged['uva_ata']), user_ata=holding(**merged['user_ata']))
    args.update(extra)
    return case(**args)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    for fee in (None, FEE_250):
        add(fee=fee)
        add(fee=fee, extra=0)
        add(fee=fee, token_program='spl', mint_owner='t22')
        add(fee=fee, token_program='spl', mint_owner='t22', uva_ata='missing')
        add(fee=fee, token_program='system', mint_owner='t22')
        add(fee=fee, token_program='system', mint_owner='system')
        add(fee=fee, token_program='system', mint_owner='t22', uva_ata='missing')
        add(fee=fee, mint_owner='spl')
        add(fee=fee, mint_owner='system')
        add(fee=fee, mint_owner='system', uva_ata='truncated')
        add(fee=fee, address_ok=False)
        add(fee=fee, address_ok=False, token_program='system', mint_owner='t22')
        # No UVA token account, or nothing in it: a no-op whatever the rest looks like.
        for empty in ('missing', holding(balance=0)):
            add(fee=fee, uva_ata=empty)
            add(fee=fee, uva_ata=empty, user_ata='missing')
            add(fee=fee, uva_ata=empty, user_ata=holding(owner_matches=False))
            add(fee=fee, uva_ata=empty, paused=True)
            add(fee=fee, uva_ata=empty, mint_truncated=True)
            add(fee=fee, uva_ata=empty, stable_claimed=U64)
        add(fee=fee, uva_ata=holding(balance=0, frozen=True))
        add(fee=fee, uva_ata=holding(balance=0, wrong_program=True))
        # Shapes of both token accounts.
        for shape in ('truncated', 'uninitialized', holding(wrong_program=True)):
            add(fee=fee, uva_ata=shape)
            add(fee=fee, uva_ata=shape, user_ata='missing')
            add(fee=fee, uva_ata=shape, user_ata=holding(owner_matches=False))
            add(fee=fee, uva_ata=shape, mint_truncated=True)
        for shape in ('missing', 'truncated', 'uninitialized', holding(wrong_program=True), holding(owner_matches=False)):
            add(fee=fee, user_ata=shape)
            add(fee=fee, user_ata=shape, uva_ata=holding(frozen=True))
            add(fee=fee, user_ata=shape, mint_truncated=True)
            add(fee=fee, user_ata=shape, paused=True)
        add(fee=fee, mint_truncated=True)
        add(fee=fee, mint_truncated=True, uva_ata=holding(frozen=True))
        add(fee=fee, mint_truncated=True, uva_ata=holding(wrong_program=True))
        # Claimed total: the transfer runs first, so its failure wins over the panic.
        add(fee=fee, stable_claimed=U64 - 500_000)
        add(fee=fee, stable_claimed=U64 - 499_999)
        add(fee=fee, stable_claimed=U64, uva_ata=holding(frozen=True))
        add(fee=fee, stable_claimed=U64, user_ata=holding(frozen=True))
        add(fee=fee, stable_claimed=U64, user_ata=holding(owner_matches=False))
        add(fee=fee, claimed=U64)
    # Transfer fee: schedule choice, rounding, cap, whole amount.
    for fee, epoch in ((FEE_250, 0), ((0, 0, 0, 250, 100), 0), ((0, 0, 0, 10_000, 10**18), 0), ((100, 10**18, 5, 250, 10**18), 4),
                       ((100, 10**18, 5, 250, 10**18), 5), ((100, 10**18, 5, 250, 10**18), 6), ((100, 17, 5, 250, 10**18), 1),
                       ((0, 0, 0, 0, 10**18), 0), ((0, 0, 0, 250, 0), 0)):
        add(fee=fee, epoch=epoch)
        add(fee=fee, epoch=epoch, uva_ata=holding(balance=U64), user_ata=holding(balance=0))
    for amount in (1, 39, 40, 41, 79, 80, 81, 400, 401, 10**9):
        add(fee=FEE_250, uva_ata=holding(balance=amount))
        add(fee=FEE_250, uva_ata=holding(balance=amount), user_ata=holding(balance=3, fee_extension=False))
    add(fee=(0, 0, 0, 0, 10**18), user_ata=holding(balance=3, fee_extension=False))
    add(fee=(0, 0, 0, 250, 0), user_ata=holding(balance=3, fee_extension=False))
    add(fee=FEE_250, uva_ata=holding(fee_extension=False))
    # Order of the token program's checks, pair by pair.
    faults = {
        'source_frozen': dict(uva_ata=dict(frozen=True)), 'source_mint': dict(uva_ata=dict(mint_matches=False)),
        'owner': dict(uva_ata=dict(owner_matches=False)), 'non_transferable': dict(uva_ata=dict(non_transferable=True)),
        'paused': dict(paused=True), 'cpi_guard': dict(uva_ata=dict(cpi_guard=True)),
        'destination_frozen': dict(user_ata=dict(frozen=True)), 'destination_mint': dict(user_ata=dict(mint_matches=False)),
        'memo': dict(user_ata=dict(memo=True)), 'no_fee_extension': dict(fee=FEE_250, user_ata=dict(fee_extension=False)),
        'hook': dict(hook_set=True), 'source_program': dict(uva_ata=dict(wrong_program=True)),
        'stranger': dict(user_ata=dict(owner_matches=False)), 'destination_program': dict(user_ata=dict(wrong_program=True)),
    }
    names = list(faults)
    for i, left in enumerate(names):
        cases.append(with_faults(faults[left]))
        for right in names[i + 1:]:
            cases.append(with_faults(faults[left], faults[right]))
    return cases


def random_cases(count=400, seed=2209):
    rng = random.Random(seed)
    cases = []

    def fee():
        if rng.random() < 0.4:
            return None
        return (rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)), rng.randrange(0, 8),
                rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)))

    def held(source):
        if rng.random() < 0.06:
            return rng.choice(('missing', 'truncated', 'uninitialized'))
        flag = lambda p: rng.random() < p
        return holding(balance=rng.choice((0, 1, rng.randrange(0, 10**7), rng.randrange(0, 10**15))) if source else rng.randrange(0, 10**6),
                       frozen=flag(0.05), fee_extension=None if flag(0.9) else flag(0.5), owner_matches=not flag(0.05),
                       mint_matches=not flag(0.05), memo=flag(0.05), cpi_guard=flag(0.05), non_transferable=flag(0.05),
                       wrong_program=flag(0.04))

    for _ in range(count):
        cases.append(case(fee=fee(), epoch=rng.randrange(0, 8), hook_set=rng.random() < 0.08, paused=rng.random() < 0.08,
                          uva_ata=held(True), user_ata=held(False), address_ok=rng.random() > 0.03,
                          mint_truncated=rng.random() < 0.05, extra=rng.choice((0, rng.randrange(1, 10**10))),
                          claimed=rng.randrange(0, 10**12), earned=rng.randrange(0, 10**12),
                          stable_claimed=rng.choice((0, rng.randrange(0, 10**12), U64 - rng.randrange(0, 10**7))),
                          mint_owner=rng.choice(('t22',) * 19 + ('system',))))
    return cases


class ClaimCashbackV2Token2022CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'claim-cashback-v2-token2022-host'
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
        _, tokens, kept, uva_hex, event_hex = answer.split(',')
        tokens, kept = int(tokens), int(kept)
        self.assertEqual(captured['lamports'], (0, 0))
        self.assertEqual(captured['uva_tokens'], -tokens)
        self.assertEqual(captured['user_tokens'], tokens - kept)
        if tokens:
            self.assertEqual(captured['withheld'], kept)
        self.assertEqual(captured['uva'].hex(), uva_hex)
        self.assertEqual([e.hex() for e in captured['events']], [] if event_hex == '-' else [event_hex])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item).replace(uva_data(item).hex(), 'uva'), host=answer[:60]):
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
        for broken in (dict(captured, withheld=captured['withheld'] + 1),
                       dict(captured, user_tokens=captured['user_tokens'] + 1),
                       dict(captured, uva=bytes(UVA_LEN))):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, broken)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'panic', 'invalid_account_data', 'uninitialized_account', 'incorrect_program_id', 'error:3', 'error:4',
            'error:13', 'error:17', 'error:36', 'error:37', 'error:42', 'error:67', 'error:2006', 'error:6010',
            'error:6064', 'error:6076',
        })


if __name__ == '__main__':
    unittest.main()
