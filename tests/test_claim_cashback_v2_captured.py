"""Captured-program checks for the recovered Pump `claim_cashback_v2`.

Every case runs Pump `claim_cashback_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token
and Associated Token programs, against a synthetic UserVolumeAccumulator (UVA),
its quote token account and the user's quote token account, on the native
(wrapped SOL mint) and SPL-token routes. The same inputs go to
`programs/pump/recovered/claim_cashback_v2_host.rs`, and the error (or panic),
the lamport and token movements, the stored UVA bytes and the
ClaimCashbackEvent must agree. This shows matching behavior on these inputs
only; it is not a byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/claim_cashback_v2_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
NATIVE_MINT = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
UVA_DISC = bytes(next(a['discriminator'] for a in IDL['accounts'] if a['name'] == 'UserVolumeAccumulator'))
IX = next(i for i in IDL['instructions'] if i['name'] == 'claim_cashback_v2')

PAYER = Keypair.from_seed(bytes([220]) * 32)
USER = Pubkey.from_bytes(bytes([28]) * 32)
QUOTE_MINT = Pubkey.from_bytes(bytes([29]) * 32)
STRANGER = Pubkey.from_bytes(bytes([30]) * 32)
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
RENT_PER_BYTE = 6960
TOKEN_RENT = 2_039_280
UVA_LEN = 137


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


EVENT_AUTHORITY = pda(b'__event_authority')
UVA = pda(b'user_volume_accumulator', bytes(USER))


def ata(owner, mint, program=TOKEN):
    return Pubkey.find_program_address([bytes(owner), bytes(program), bytes(mint)], ATA)[0]


def rent(size):
    return (128 + size) * RENT_PER_BYTE


DEFAULTS = dict(native=False, extra=1_000_000, claimed=7_000, stable_claimed=8_000, earned=9_000_000,
                stable_earned=10_000_000, uva_ata=500_000, token_program='token', mint_owner='token',
                quote_user='ok', quote_user_balance=3)


def case(**changes):
    return dict(DEFAULTS, **changes)


def uva_data(item):
    data = bytearray((i * 37 + 11) % 256 for i in range(UVA_LEN))
    head = UVA_DISC + bytes(USER) + bytes([1]) + struct.pack('<QQQq', 5, 6, 7, TIMESTAMP - 50) + bytes([1])
    head += struct.pack('<QQQQ', item['earned'], item['claimed'], item['stable_earned'], item['stable_claimed'])
    data[:len(head)] = head
    return bytes(data)


def mint_data():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**15) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(mint, owner, amount):
    return (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(USER, Account(10**9, b'', SYSTEM))
    vm.set_account(UVA, Account(rent(UVA_LEN) + item['extra'], uva_data(item), PUMP))
    mint = NATIVE_MINT if item['native'] else QUOTE_MINT
    program = {'token': TOKEN, 'system': SYSTEM}[item['token_program']]
    vm.set_account(mint, Account(10**9, mint_data(), {'token': TOKEN, 'system': SYSTEM}[item['mint_owner']]))
    uva_ata = ata(UVA, mint, program)
    if item['uva_ata'] is not None:
        vm.set_account(uva_ata, Account(TOKEN_RENT, token_data(mint, UVA, item['uva_ata']), TOKEN))
    user_ata = ata(USER, mint)
    if item['quote_user'] != 'absent':
        owner = STRANGER if item['quote_user'] == 'stranger' else USER
        vm.set_account(user_ata, Account(TOKEN_RENT, token_data(mint, owner, item['quote_user_balance']), TOKEN))
    named = {'user': USER, 'user_volume_accumulator': UVA, 'quote_mint': mint, 'quote_token_program': program,
             'associated_token_program': ATA, 'associated_user_volume_accumulator': uva_ata,
             'associated_quote_user': user_ata, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY,
             'program': PUMP}
    metas = [AccountMeta(named[a['name']], False, a.get('writable', False)) for a in IX['accounts']]
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0] if vm.get_account(key) else None
    before = (lamports(USER), lamports(UVA))
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, bytes(IX['discriminator']), metas)], PAYER.pubkey(),
                                           [PAYER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        if code:
            return {'error': int(code.group(1))}
        return {'error': 'panic' if any('panicked' in l for l in result.meta().logs()) else text}
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'delta': (lamports(USER) - before[0], lamports(UVA) - before[1]),
            'tokens': (tokens(uva_ata), tokens(user_ata)), 'uva': bytes(vm.get_account(UVA).data), 'events': events}


def host_line(item):
    quote_user = {'ok': 'user', 'stranger': 'stranger', 'absent': 'absent'}[item['quote_user']]
    fields = [bytes(USER).hex(), int(item['native']), int(item['token_program'] == 'token'),
              int(item['mint_owner'] == item['token_program']), '-' if item['uva_ata'] is None else item['uva_ata'],
              quote_user, rent(UVA_LEN) + item['extra'], uva_data(item).hex(), TIMESTAMP]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    # Native route: lamports above rent; token accounts and program unchecked.
    for extra in (0, 1, 1_000_000):
        add(native=True, extra=extra)
    add(native=True, token_program='system')
    add(native=True, mint_owner='system')
    add(native=True, uva_ata=None, quote_user='absent')
    add(native=True, quote_user='stranger')
    add(native=True, claimed=U64 - 1_000_000)
    add(native=True, claimed=U64 - 999_999)
    add(native=True, claimed=U64, extra=0)
    add(native=True, stable_claimed=U64)
    # Token route.
    add()
    add(extra=0)
    for balance in (None, 0, 1, U64):
        add(uva_ata=balance)
    add(token_program='system')
    add(token_program='system', uva_ata=None)
    add(mint_owner='system')
    add(mint_owner='system', uva_ata=None)
    add(quote_user='absent')
    add(quote_user='stranger')
    add(quote_user='absent', uva_ata=None)
    add(quote_user='stranger', uva_ata=0)
    add(quote_user_balance=U64 - 500_000)
    add(stable_claimed=U64 - 500_000)
    add(stable_claimed=U64 - 499_999)
    add(stable_claimed=U64, uva_ata=0)
    add(claimed=U64, earned=0)
    return cases


def random_cases(count=50, seed=3522):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        cases.append(case(native=rng.random() < 0.4, extra=rng.choice((0, rng.randrange(1, 10**10))),
                          claimed=rng.choice((0, rng.randrange(0, 10**12), U64 - rng.randrange(0, 10**10))),
                          stable_claimed=rng.choice((0, rng.randrange(0, 10**12), rng.randrange(0, 10**12), U64 - rng.randrange(0, 10**7))),
                          earned=rng.randrange(0, 10**12), uva_ata=rng.choice((None, 0) + (rng.randrange(1, 10**7),) * 4),
                          token_program='token' if rng.random() < 0.9 else 'system',
                          mint_owner='token' if rng.random() < 0.9 else 'system',
                          quote_user=rng.choice(('ok', 'ok', 'ok', 'stranger', 'absent')),
                          quote_user_balance=rng.randrange(0, 10**9)))
    return cases


class ClaimCashbackV2CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'claim-cashback-v2-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer == 'panic':
            self.assertEqual(captured['error'], 'panic')
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        _, lamports, tokens, uva_hex, event_hex = answer.split(',')
        lamports, tokens = int(lamports), int(tokens)
        self.assertEqual(captured['delta'], (lamports, -lamports))
        uva_ata = None if item['uva_ata'] is None else item['uva_ata'] - tokens
        user_ata = None if item['quote_user'] == 'absent' else item['quote_user_balance'] + tokens
        self.assertEqual(captured['tokens'], (uva_ata, user_ata))
        self.assertEqual(captured['uva'].hex(), uva_hex)
        self.assertEqual([e.hex() for e in captured['events']], [] if event_hex == '-' else [event_hex])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=item, host=answer[:40]):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_missing_token_movement(self):
        # Negative control: a passing token-route claim must fail once the
        # token movement is undone.
        item = case()
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(item, answer, dict(captured, tokens=(item['uva_ata'], item['quote_user_balance'])))

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers}, {'ok', 'panic', 'error:6010', 'error:6064', 'error:6076'})


if __name__ == '__main__':
    unittest.main()
