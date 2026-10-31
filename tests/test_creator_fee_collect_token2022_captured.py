"""Captured-program checks for Pump creator-fee collection on Token-2022 quotes.

Every case runs Pump `collect_creator_fee_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs, against synthetic creator, vault and
token accounts on a mint with Token-2022 extensions. The same inputs go to
`programs/pump/recovered/creator_fee_collect_token2022_host.rs`, and the error,
token movements, withheld amount, and the CollectCreatorFeeEvent log and its
self-CPI copy must agree. This shows matching behavior on these inputs only; it
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
RELAY_ELF = DEPS / 'donation_relay/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_fee_collect_token2022_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
EVENT_IX_TAG = bytes([228, 69, 165, 46, 81, 203, 154, 29])

PAYER = Keypair.from_seed(bytes([223]) * 32)
CREATOR = Pubkey.from_bytes(bytes([41]) * 32)
QUOTE = Pubkey.from_bytes(bytes([42]) * 32)
EXECUTABLE = Pubkey.from_bytes(bytes([43]) * 32)  # an unrelated captured program
OTHER = Pubkey.from_bytes(bytes([44]) * 32)
WRONG_ATA = Pubkey.from_bytes(bytes([45]) * 32)
TX_FEE = 5000
ZERO_RENT = 890_880
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
FEE_250 = (0, 0, 0, 250, 10**18)
PROGRAMS = {'t22': TOKEN22, 'spl': TOKEN, 'other': OTHER}


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


EVENT_AUTHORITY = pda([b'__event_authority'])


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint_data(item):
    base = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)
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


HOLDING = dict(balance=10**6, frozen=False, fee_extension=None, owner_matches=True, mint_matches=True, memo=False,
               cpi_guard=False, non_transferable=False, wrong_program=False)


def holding(**changes):
    return dict(HOLDING, **changes)


def token_data(holder, owner, fallback_fee_extension):
    held = HOLDING if isinstance(holder, str) else holder
    fee_extension = fallback_fee_extension if held['fee_extension'] is None else held['fee_extension']
    data = (bytes(QUOTE if held['mint_matches'] else OTHER) + bytes(owner if held['owner_matches'] else OTHER)
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


DEFAULTS = dict(creator='system', token_program='t22', mint_owner='t22', fee=None, epoch=0, hook_set=False, paused=False,
                addresses_ok=True, vault_ata=None, creator_ata=None)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['vault_ata'] is None:
        item['vault_ata'] = holding()
    if item['creator_ata'] is None:
        item['creator_ata'] = holding(balance=0)
    return item


def host_ata(item, held):
    if isinstance(held, str):
        return held
    fee_extension = bool(item['fee']) if held['fee_extension'] is None else held['fee_extension']
    text = ':'.join(str(int(v)) for v in (held['balance'], held['frozen'], fee_extension, held['owner_matches'],
                                          held['mint_matches'], held['memo'], held['cpi_guard'], held['non_transferable']))
    return 'wrong:' + text if held['wrong_program'] else text


def host_line(item):
    fee = ':'.join(str(v) for v in item['fee']) if item['fee'] else '-'
    fields = [int(item['creator'] == 'fees'), int(item['creator'] == 'program'), item['token_program'], item['mint_owner'],
              fee, item['epoch'], int(item['hook_set']), int(item['paused']), int(item['addresses_ok']),
              host_ata(item, item['vault_ata']), host_ata(item, item['creator_ata'])]
    return ','.join(str(f) for f in fields)


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name in ('InvalidAccountData', 'UninitializedAccount', 'IncorrectProgramId'):
        if name in text:
            return re.sub(r'(?<!^)([A-Z])', r'_\1', name).lower()
    return text


def flat(data):
    # solders JSON writes a byte vector as [[compact length], b0, b1, ...].
    return bytes(data[1:]) if data and isinstance(data[0], list) else bytes(data)


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
        for key, path in ((PUMP, PUMP_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF), (EXECUTABLE, RELAY_ELF)):
            self.vm.add_program_from_file(key, path)
        self.stale = set()

    def run(self, item):
        vm = self.vm
        vm.set_clock(Clock(100, TIMESTAMP, item['epoch'], 0, TIMESTAMP))
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        program = PROGRAMS[item['token_program']]
        creator = EXECUTABLE if item['creator'] == 'program' else CREATOR
        vault = pda([b'creator-vault', bytes(creator)])
        creator_ata = pda([bytes(creator), bytes(program), bytes(QUOTE)], ATA)
        vault_ata = pda([bytes(vault), bytes(program), bytes(QUOTE)], ATA)
        owner = {'t22': TOKEN22, 'spl': TOKEN, 'other': SYSTEM}[item['mint_owner']]
        accounts = {PAYER.pubkey(): Account(10**12, b'', SYSTEM), QUOTE: Account(10**10, mint_data(item), owner),
                    vault: Account(ZERO_RENT + 10**6, b'', SYSTEM)}
        if item['creator'] != 'program':
            accounts[creator] = Account(10**9, b'', FEES if item['creator'] == 'fees' else SYSTEM)
        token_owner = program if program != OTHER else TOKEN22
        for key, holder, authority in ((vault_ata, item['vault_ata'], vault), (creator_ata, item['creator_ata'], creator)):
            if holder == 'missing':
                continue
            wrong = not isinstance(holder, str) and holder['wrong_program']
            account_owner = (TOKEN if token_owner == TOKEN22 else TOKEN22) if wrong else token_owner
            accounts[key] = Account(10**8, token_data(holder, authority, bool(item['fee'])), account_owner)
        for key, account in accounts.items():
            vm.set_account(key, account)
        self.stale = {k for k in accounts if k != PAYER.pubkey()} | {vault_ata, creator_ata}
        names = {'creator': creator, 'creator_vault': vault, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY,
                 'program': PUMP, 'creator_token_account': creator_ata if item['addresses_ok'] else WRONG_ATA,
                 'creator_vault_token_account': vault_ata, 'quote_mint': QUOTE, 'quote_token_program': program,
                 'associated_token_program': ATA}
        ix = IX['collect_creator_fee_v2']
        metas = [AccountMeta(names[a['name']], False, a.get('writable', False)) for a in ix['accounts']]

        def lamports(key):
            account = vm.get_account(key)
            return account.lamports if account else 0

        def data(key):
            account = vm.get_account(key)
            return bytes(account.data) if account else b''

        def tokens(key):
            raw = data(key)
            return struct.unpack_from('<Q', raw, 64)[0] if len(raw) >= 72 else 0

        watched = [PAYER.pubkey(), vault, creator]
        before = [lamports(k) for k in watched]
        vault_before, creator_before = tokens(vault_ata), tokens(creator_ata)
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                               [PAYER], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return {'error': error_name(str(result.err()))}
        inner = json.loads(result.to_json()).get('inner_instructions') or [[]]
        return {'error': None, 'lamports': [lamports(k) - b for k, b in zip(watched, before)],
                'vault_tokens': tokens(vault_ata) - vault_before, 'creator_tokens': tokens(creator_ata) - creator_before,
                'withheld': withheld(data(creator_ata)),
                'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')],
                'self_cpi': [d for d in (flat(i['instruction']['data']) for i in inner[0]) if d.startswith(EVENT_IX_TAG)]}


def with_faults(*faults):
    merged = dict(vault_ata={}, creator_ata=dict(balance=0))
    extra = {}
    for fault in faults:
        for key, value in fault.items():
            if key in merged and isinstance(value, dict):
                merged[key] = dict(merged[key], **value)
            else:
                extra[key] = value
    args = dict(vault_ata=holding(**merged['vault_ata']), creator_ata=holding(**merged['creator_ata']))
    args.update(extra)
    return case(**args)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    for fee in (None, FEE_250):
        add(fee=fee)
        for creator in ('fees', 'program'):
            add(fee=fee, creator=creator)
            add(fee=fee, creator=creator, vault_ata='missing')
            add(fee=fee, creator=creator, vault_ata=holding(balance=0))
            add(fee=fee, creator=creator, creator_ata='missing')
            add(fee=fee, creator=creator, paused=True)
            add(fee=fee, creator=creator, addresses_ok=False)
            add(fee=fee, creator=creator, mint_owner='other')
            add(fee=fee, creator=creator, token_program='other')
        # A zero balance ends before the creator ATA or the mint state is seen.
        for creator_ata in ('missing', 'truncated', 'uninitialized', holding(wrong_program=True), holding(frozen=True)):
            add(fee=fee, vault_ata=holding(balance=0), creator_ata=creator_ata)
        add(fee=fee, vault_ata=holding(balance=0), paused=True)
        add(fee=fee, vault_ata=holding(balance=0), hook_set=True)
        add(fee=fee, vault_ata=holding(balance=0, frozen=True))
        add(fee=fee, vault_ata=holding(balance=0, wrong_program=True))
        add(fee=fee, vault_ata=holding(balance=0, mint_matches=False))
        add(fee=fee, vault_ata=holding(balance=0, owner_matches=False))
        # Vault and creator ATA shapes.
        for shape in ('missing', 'truncated', 'uninitialized', holding(wrong_program=True)):
            add(fee=fee, vault_ata=shape)
            add(fee=fee, creator_ata=shape)
            add(fee=fee, vault_ata=shape, creator_ata='missing')
            add(fee=fee, vault_ata=shape, addresses_ok=False)
            add(fee=fee, creator_ata=shape, vault_ata=holding(frozen=True))
        add(fee=fee, addresses_ok=False)
        add(fee=fee, mint_owner='other')
        add(fee=fee, mint_owner='other', addresses_ok=False)
        add(fee=fee, token_program='other')
        add(fee=fee, token_program='other', mint_owner='other')
        add(fee=fee, token_program='other', addresses_ok=False)
        add(fee=fee, mint_owner='spl')
        add(fee=fee, mint_owner='spl', vault_ata=holding(frozen=True))
        add(fee=fee, mint_owner='spl', creator_ata='missing')
        add(fee=fee, mint_owner='spl', vault_ata=holding(owner_matches=False))
        add(fee=fee, token_program='spl')
        add(fee=fee, token_program='spl', vault_ata=holding(frozen=True, fee_extension=False))
        add(fee=fee, token_program='spl', vault_ata=holding(fee_extension=False))
        add(fee=fee, token_program='spl', vault_ata=holding(fee_extension=False), creator_ata=holding(balance=0, fee_extension=False))
    # Transfer fee: schedule choice, rounding, cap, whole amount.
    for fee, epoch in ((FEE_250, 0), ((0, 0, 0, 250, 100), 0), ((0, 0, 0, 10_000, 10**18), 0), ((100, 10**18, 5, 250, 10**18), 4),
                       ((100, 10**18, 5, 250, 10**18), 5), ((100, 10**18, 5, 250, 10**18), 6), ((100, 17, 5, 250, 10**18), 1),
                       ((0, 0, 0, 0, 10**18), 0), ((0, 0, 0, 250, 0), 0)):
        add(fee=fee, epoch=epoch)
        add(fee=fee, epoch=epoch, vault_ata=holding(balance=U64))
    for amount in (1, 39, 40, 41, 79, 80, 81, 400, 401, 10**9):
        add(fee=FEE_250, vault_ata=holding(balance=amount))
        add(fee=FEE_250, vault_ata=holding(balance=amount), creator_ata=holding(balance=0, fee_extension=False))
    add(fee=(0, 0, 0, 0, 10**18), creator_ata=holding(balance=0, fee_extension=False))
    add(fee=(0, 0, 0, 250, 0), creator_ata=holding(balance=0, fee_extension=False))
    add(fee=FEE_250, vault_ata=holding(fee_extension=False))
    # Order of the token program's checks, pair by pair.
    faults = {
        'source_frozen': dict(vault_ata=dict(frozen=True)), 'source_mint': dict(vault_ata=dict(mint_matches=False)),
        'mint_owner': dict(mint_owner='spl'), 'owner': dict(vault_ata=dict(owner_matches=False)),
        'non_transferable': dict(vault_ata=dict(non_transferable=True)), 'paused': dict(paused=True),
        'cpi_guard': dict(vault_ata=dict(cpi_guard=True)), 'destination_frozen': dict(creator_ata=dict(frozen=True)),
        'destination_mint': dict(creator_ata=dict(mint_matches=False)), 'memo': dict(creator_ata=dict(memo=True)),
        'no_fee_extension': dict(fee=FEE_250, creator_ata=dict(fee_extension=False)), 'hook': dict(hook_set=True),
        'source_program': dict(vault_ata=dict(wrong_program=True)),
        'destination_program': dict(creator_ata=dict(wrong_program=True)),
        'destination_missing': dict(creator_ata='missing'), 'destination_short': dict(creator_ata='truncated'),
        'destination_unset': dict(creator_ata='uninitialized'),
    }
    names = list(faults)
    for i, left in enumerate(names):
        cases.append(with_faults(faults[left]))
        for right in names[i + 1:]:
            if isinstance(faults[left].get('creator_ata'), str) and 'creator_ata' in faults[right]:
                continue
            if isinstance(faults[right].get('creator_ata'), str) and 'creator_ata' in faults[left]:
                continue
            cases.append(with_faults(faults[left], faults[right]))
    return cases


def random_cases(count=400, seed=2208):
    rng = random.Random(seed)
    cases = []

    def fee():
        if rng.random() < 0.4:
            return None
        return (rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)), rng.randrange(0, 8),
                rng.randrange(0, 10_001), rng.choice((0, rng.randrange(0, 10**6), U64)))

    def held(source):
        if rng.random() < 0.08:
            return rng.choice(('missing', 'truncated', 'uninitialized'))
        flag = lambda p: rng.random() < p
        return holding(balance=rng.choice((0, 1, rng.randrange(0, 10**7), rng.randrange(0, 10**15))) if source else rng.randrange(0, 10**6),
                       frozen=flag(0.07), fee_extension=None if flag(0.9) else flag(0.5), owner_matches=not (source and flag(0.05)),
                       mint_matches=not flag(0.05), memo=flag(0.07), cpi_guard=flag(0.07), non_transferable=flag(0.07),
                       wrong_program=flag(0.04))

    for _ in range(count):
        cases.append(case(creator=rng.choice(('system',) * 18 + ('fees', 'program')), fee=fee(), epoch=rng.randrange(0, 8),
                          hook_set=rng.random() < 0.1, paused=rng.random() < 0.1, vault_ata=held(True), creator_ata=held(False),
                          addresses_ok=rng.random() > 0.03, mint_owner=rng.choice(('t22',) * 18 + ('spl', 'other')),
                          token_program=rng.choice(('t22',) * 19 + ('other',))))
    return cases


class CreatorFeeCollectToken2022CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-fee-collect-token2022-host'
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
        tokens, kept, event = map(int, answer.split(',')[1:])
        self.assertEqual(captured['lamports'], [-TX_FEE, 0, 0])
        self.assertEqual(captured['vault_tokens'], -tokens)
        self.assertEqual(captured['creator_tokens'], tokens - kept)
        if tokens:
            self.assertEqual(captured['withheld'], kept)
        if event:
            creator = EXECUTABLE if item['creator'] == 'program' else CREATOR
            payload = (EVENT_DISC['CollectCreatorFeeEvent'] + struct.pack('<q', TIMESTAMP) + bytes(creator)
                       + struct.pack('<Q', tokens) + bytes(QUOTE))
            self.assertEqual(captured['events'], [payload])
            self.assertEqual(captured['self_cpi'], [EVENT_IX_TAG + payload])
        else:
            self.assertEqual((captured['events'], captured['self_cpi']), ([], []))

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
        for broken in (dict(captured, withheld=captured['withheld'] + 1),
                       dict(captured, creator_tokens=captured['creator_tokens'] + 1),
                       dict(captured, vault_tokens=-captured['vault_tokens'])):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, broken)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'invalid_account_data', 'uninitialized_account', 'incorrect_program_id', 'error:3', 'error:4',
            'error:13', 'error:17', 'error:36', 'error:37', 'error:42', 'error:67', 'error:2006', 'error:3007',
            'error:3008', 'error:6050',
        })


if __name__ == '__main__':
    unittest.main()
