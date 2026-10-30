"""Captured-program checks for the recovered Pump creator-fee collection.

Every case runs Pump `collect_creator_fee` or `collect_creator_fee_v2` (WSOL
and SPL quote mints) from the captured `evidence/original/pump/deployed.so`
on LiteSVM, with the captured SPL Token and Associated Token programs, against
synthetic creator, creator-vault and token accounts. The same inputs go to
`programs/pump/recovered/creator_fee_collect_host.rs`, and the error, signed
lamport and token movements, the CollectCreatorFeeEvent log and its self-CPI
copy must agree. This shows matching behavior on these inputs only; it is not
a byte-identity claim.
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
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/creator_fee_collect_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
EVENT_IX_TAG = bytes([228, 69, 165, 46, 81, 203, 154, 29])

PAYER = Keypair.from_seed(bytes([222]) * 32)
CREATOR = Pubkey.from_bytes(bytes([41]) * 32)
QUOTE = Pubkey.from_bytes(bytes([42]) * 32)
# An unrelated captured program loaded at this address stands in for an
# executable creator (the invoked Pump id itself is demoted to read-only).
EXECUTABLE = Pubkey.from_bytes(bytes([43]) * 32)
TX_FEE = 5000
ZERO_RENT = 890_880
TOKEN_RENT = 2_039_280
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


EVENT_AUTHORITY = pda([b'__event_authority'])


def rent(data_len):
    return (128 + data_len) * 6960


def mint_data(decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + bytes(36) + bytes([1]) + bytes(56)


DEFAULTS = dict(op='v1', creator='system', lamports=10**9, data_len=0, vault=ZERO_RENT + 10**6,
                vault_tokens=None, creator_ata=True)


def case(**changes):
    item = dict(DEFAULTS, **changes)
    if item['op'] == 'v2_spl' and 'vault_tokens' not in changes:
        item['vault_tokens'] = 10**6
    return item


def creator_key(item):
    return EXECUTABLE if item['creator'] == 'program' else CREATOR


def quote_mint(item):
    return WSOL if item['op'] == 'v2_sol' else QUOTE


def flat(data):
    # solders JSON writes a byte vector as [[compact length], b0, b1, ...].
    return bytes(data[1:]) if data and isinstance(data[0], list) else bytes(data)


def error_name(text):
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return code.group(1)
    for name in ('InvalidAccountData', 'ArithmeticOverflow'):
        if name in text:
            return re.sub(r'(?<!^)([A-Z])', r'_\1', name).lower()
    return text


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    for name, key in (('spl_token', TOKEN), ('associated_token', ATA)):
        vm.add_program_from_file(key, DEPS / name / 'deployed.so')
    vm.add_program_from_file(EXECUTABLE, DEPS / 'donation_relay/deployed.so')
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    creator = creator_key(item)
    if item['creator'] != 'program' and item['lamports']:
        owner = {'system': SYSTEM, 'fees': FEES, 'token': TOKEN}[item['creator']]
        vm.set_account(creator, Account(item['lamports'], bytes(item['data_len']), owner))
    vault = pda([b'creator-vault', bytes(creator)])
    if item['vault']:
        vm.set_account(vault, Account(item['vault'], b'', SYSTEM))
    names = {'creator': creator, 'creator_vault': vault, 'system_program': SYSTEM,
             'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    token_accounts = []
    if item['op'] != 'v1':
        quote = quote_mint(item)
        vm.set_account(quote, Account(10**9, mint_data(9 if quote == WSOL else 6), TOKEN))
        creator_ata = pda([bytes(creator), bytes(TOKEN), bytes(quote)], ATA)
        vault_ata = pda([bytes(vault), bytes(TOKEN), bytes(quote)], ATA)
        if item['vault_tokens'] is not None:
            vm.set_account(vault_ata, Account(TOKEN_RENT, token_data(quote, vault, item['vault_tokens']), TOKEN))
        if item['creator_ata']:
            vm.set_account(creator_ata, Account(TOKEN_RENT, token_data(quote, creator, 0), TOKEN))
        names.update(creator_token_account=creator_ata, creator_vault_token_account=vault_ata, quote_mint=quote,
                     quote_token_program=TOKEN, associated_token_program=ATA)
        token_accounts = [vault_ata, creator_ata]
    ix = IX['collect_creator_fee' if item['op'] == 'v1' else 'collect_creator_fee_v2']
    metas = [AccountMeta(names[a['name']], False, a.get('writable', False)) for a in ix['accounts']]

    def lamports(key):
        account = vm.get_account(key)
        return account.lamports if account else 0

    def tokens(key):
        account = vm.get_account(key)
        return struct.unpack_from('<Q', bytes(account.data), 64)[0] if account else 0

    watched = [PAYER.pubkey(), vault, creator]
    before = [lamports(k) for k in watched]
    tokens_before = [tokens(k) for k in token_accounts]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(ix['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        return {'error': error_name(str(result.err()))}
    # Signed after - before for every watched lamport and token balance.
    delta = [lamports(k) - b for k, b in zip(watched, before)]
    token_delta = [tokens(k) - b for k, b in zip(token_accounts, tokens_before)] or [0, 0]
    inner = json.loads(result.to_json()).get('inner_instructions') or [[]]
    return {'error': None, 'payer': delta[0], 'vault': delta[1], 'creator': delta[2],
            'vault_tokens': token_delta[0], 'creator_tokens': token_delta[1],
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')],
            'self_cpi': [d for d in (flat(i['instruction']['data']) for i in inner[0]) if d.startswith(EVENT_IX_TAG)]}


def host_line(item):
    executable = item['creator'] == 'program'
    if item['op'] == 'v2_spl':
        tokens = '-' if item['vault_tokens'] is None else item['vault_tokens']
        quote = f"spl:{tokens}:{int(item['creator_ata'])}"
    else:
        quote = 'native'
    lamports = 0 if executable else item['lamports']
    data_len = item['data_len'] if lamports else 0
    # A creator with no lamports does not exist, so it is not owned by Pump Fees.
    fields = [int(item['creator'] == 'fees' and lamports > 0), int(executable), lamports, data_len, item['vault'], quote]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    for op in ('v1', 'v2_sol', 'v2_spl'):
        add(op=op)
        # Vault lamports around the zero-byte reserve (ignored on the SPL path).
        for vault in (0, 1, ZERO_RENT - 1, ZERO_RENT, ZERO_RENT + 1, U64):
            add(op=op, vault=vault)
        # Creator kinds: Pump Fees owned, executable, other owner, missing.
        for creator in ('fees', 'program', 'token'):
            add(op=op, creator=creator)
            add(op=op, creator=creator, vault=0)
        add(op=op, creator='fees', vault_tokens=None)
        add(op=op, creator='program', vault_tokens=0)
        add(op=op, creator='token', lamports=1, data_len=165)
        add(op=op, lamports=0)
        # Creator rent shortfall: lamports + amount against rent(data_len).
        for extra in (-1, 0, 1):
            add(op=op, lamports=0, vault=2 * ZERO_RENT + extra)
            add(op=op, lamports=1, data_len=10, vault=ZERO_RENT + rent(10) - 1 + extra)
            add(op=op, lamports=rent(300) - 5000, data_len=300, vault=ZERO_RENT + 5000 + extra)
            add(op=op, creator='token', lamports=rent(165) - 1, data_len=165, vault=ZERO_RENT + 1 + extra)
        add(op=op, lamports=rent(10_000), data_len=10_000, vault=ZERO_RENT + 1)
        # Creator credit overflow.
        add(op=op, lamports=U64 - 10**6, vault=ZERO_RENT + 10**6)
        add(op=op, lamports=U64 - 10**6, vault=ZERO_RENT + 10**6 + 1)
    # SPL path: vault ATA balance and the creator ATA.
    for tokens in (None, 0, 1, U64):
        for creator_ata in (True, False):
            add(op='v2_spl', vault_tokens=tokens, creator_ata=creator_ata)
            add(op='v2_spl', vault_tokens=tokens, creator_ata=creator_ata, vault=0, lamports=0)
            add(op='v2_spl', vault_tokens=tokens, creator_ata=creator_ata, creator='program')
    add(op='v2_spl', vault_tokens=5, creator='token', lamports=1, data_len=165)
    return cases


def random_cases(count=60, seed=1717):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        data_len = rng.choice((0, 0, rng.randrange(1, 400)))
        lamports = rng.choice((0, 10**9, rng.randrange(1, 2 * rent(data_len) + 2), rng.randrange(1, 10**7)))
        cases.append(case(op=rng.choice(('v1', 'v2_sol', 'v2_spl')),
                          creator=rng.choice(('system',) * 12 + ('fees', 'program', 'token', 'token')),
                          lamports=lamports, data_len=data_len,
                          vault=rng.choice((0, rng.randrange(0, 2 * ZERO_RENT), ZERO_RENT + rng.randrange(0, 4 * 10**6),
                                            ZERO_RENT + rng.randrange(0, 10**12))),
                          vault_tokens=rng.choice((None, 0, rng.randrange(1, 10**12), rng.randrange(1, 10**12))),
                          creator_ata=rng.random() < 0.85))
    return cases


class CreatorFeeCollectCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'creator-fee-collect-host'
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
            self.assertEqual(captured['error'], answer[6:])
            return
        self.assertIsNone(captured['error'])
        lamports, tokens, event = map(int, answer.split(',')[1:])
        # Signed after - before: the vault pays, the creator receives.
        self.assertEqual(captured['payer'], -TX_FEE)
        self.assertEqual(captured['vault'], -lamports)
        self.assertEqual(captured['creator'], lamports)
        self.assertEqual(captured['vault_tokens'], -tokens)
        self.assertEqual(captured['creator_tokens'], tokens)
        if event:
            quote = QUOTE if item['op'] == 'v2_spl' else SYSTEM
            payload = (EVENT_DISC['CollectCreatorFeeEvent'] + struct.pack('<q', TIMESTAMP) + bytes(creator_key(item))
                       + struct.pack('<Q', lamports or tokens) + bytes(quote))
            self.assertEqual(captured['events'], [payload])
            self.assertEqual(captured['self_cpi'], [EVENT_IX_TAG + payload])
        else:
            self.assertEqual((captured['events'], captured['self_cpi']), ([], []))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=item, host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_reversed_balance_movements(self):
        # Negative control: passing captured collections must fail once the
        # vault debit or the creator credit is reversed.
        for item, fields in ((case(), ('vault', 'creator')), (case(op='v2_spl'), ('vault_tokens', 'creator_tokens'))):
            answer = self.host_answers([item])[0]
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            for field in fields:
                with self.subTest(op=item['op'], field=field):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, answer, dict(captured, **{field: -captured[field]}))

    def test_fixed_cases_cover_every_outcome(self):
        cases = fixed_cases()
        answers = self.host_answers(cases)
        for op in ('v1', 'v2_sol', 'v2_spl'):
            seen = {a if a.startswith('error') else 'ok' + a.split(',')[3] for c, a in zip(cases, answers) if c['op'] == op}
            expected = {'ok0', 'ok1', 'error:6050'}
            expected.add('error:invalid_account_data' if op == 'v2_spl' else 'error:arithmetic_overflow')
            self.assertEqual(seen, expected, op)


if __name__ == '__main__':
    unittest.main()
