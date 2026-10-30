"""Captured-program checks for SOL-quote holder payouts.

Every case runs Pump `distribute_fee_to_holders` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the wrapped-SOL quote
(lamports paid straight out of the `holder-rewards` PDA), plus the two
token-quote outcomes that need no token account. The same inputs go to
`programs/pump/recovered/holder_distribution_host.rs`. The error, the signed
lamport deltas of the PDA, the claim authority and every wallet, and the
full `DistributeFeeToHoldersEvent` bytes must agree. This shows matching
behaviour on these inputs only; it is not a byte-identity claim.
`scripts/pump_holder_distribution_differential.py` already compares
candidate builds with the captured program over the token paths; this is a
deterministic model of the SOL path.
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
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/holder_distribution_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
STABLE = Pubkey.from_bytes(bytes([41]) * 32)
MINT = Pubkey.from_bytes(bytes([31]) * 32)
ELSEWHERE = Pubkey.from_bytes(bytes([99]) * 32)
EXTRA = Pubkey.from_bytes(bytes([98]) * 32)
IX = next(i for i in IDL['instructions'] if i['name'] == 'distribute_fee_to_holders')
GLOBAL_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'Global')
EVENT_DISC = next(bytes(e['discriminator']) for e in IDL['events'] if e['name'] == 'DistributeFeeToHoldersEvent')

PAYER = Keypair.from_seed(bytes([201]) * 32)
AUTHORITY = Keypair.from_seed(bytes([202]) * 32)
WALLETS = {i: Pubkey.from_bytes(bytes([70 + i]) * 32) for i in range(10)}
READONLY = (8, 9)  # ids only ever passed read-only
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
REWARDS = Pubkey.find_program_address([b'holder-rewards', bytes(MINT)], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_000
FLOOR = 890_880
WALLET_LAMPORTS = 890_880
MAX = 2**64 - 1


def ata(wallet):
    return Pubkey.find_program_address([bytes(wallet), bytes(TOKEN), bytes(WSOL)], ATA_PROGRAM)[0]


def case(*entries, **changes):
    item = dict(signed=True, authority_ok=True, address_ok=True, quote='native', lamports=10**9, accounts=None,
                entries=tuple(entries), enabled=True)
    item.update(changes)
    if item['accounts'] is None:
        item['accounts'] = 2 * len(item['entries'])
    return item


def entry_text(payee, amount):
    if payee == 'r':
        return f'r:{amount}'
    return f'{"ro" if payee in READONLY else "w"}{payee}:{amount}'


def host_line(item):
    entries = '+'.join(entry_text(p, a) for p, a in item['entries']) or '-'
    return ','.join(map(str, (int(item['signed']), int(item['authority_ok']), int(item['address_ok']),
                              item['quote'], item['lamports'], item['accounts'], entries)))


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(AUTHORITY.pubkey(), Account(10**10, b'', SYSTEM))
    global_data = bytearray(1088)
    global_data[:8] = GLOBAL_DISC
    global_data[8] = 1
    global_data[1054:1086] = bytes(AUTHORITY.pubkey() if item['authority_ok'] else ELSEWHERE)
    global_data[1086] = int(item['enabled'])
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    mint_data = bytearray(82)
    mint_data[44] = 6
    mint_data[45] = 1
    vm.set_account(MINT, Account(1_461_600, bytes(mint_data), TOKEN))
    vm.set_account(WSOL, Account(1_461_600, bytes(mint_data), TOKEN))
    if item['quote'] == 'token':
        vm.set_account(STABLE, Account(1_461_600, bytes(mint_data), TOKEN))
    rewards = REWARDS if item['address_ok'] else ELSEWHERE
    if item['lamports']:
        vm.set_account(rewards, Account(item['lamports'], b'', SYSTEM))
    for wallet in WALLETS.values():
        vm.set_account(wallet, Account(WALLET_LAMPORTS, b'', SYSTEM))
    names = {'global': GLOBAL, 'holder_reward_claim_authority': AUTHORITY.pubkey(), 'mint': MINT,
             'holder_rewards': rewards, 'holder_rewards_token_account': PUMP,
             'quote_mint': WSOL if item['quote'] == 'native' else STABLE, 'quote_token_program': TOKEN,
             'associated_token_program': ATA_PROGRAM, 'system_program': SYSTEM,
             'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = [AccountMeta(names[a['name']], a.get('signer', False) and item['signed'], a.get('writable', False))
             for a in IX['accounts']]
    remaining = []
    for payee, _ in item['entries']:
        wallet = REWARDS if payee == 'r' else WALLETS[payee]
        remaining += [AccountMeta(wallet, False, payee not in READONLY), AccountMeta(ata(wallet), False, True)]
    remaining += [AccountMeta(EXTRA, False, True)] * max(0, item['accounts'] - len(remaining))
    metas += remaining[:item['accounts']]
    data = (bytes(IX['discriminator']) + len(item['entries']).to_bytes(4, 'little')
            + b''.join(struct.pack('<Q', amount) for _, amount in item['entries']))
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)], PAYER.pubkey(),
        [PAYER] + ([AUTHORITY] if item['signed'] else []), vm.latest_blockhash())
    watched = [REWARDS, AUTHORITY.pubkey()] + list(WALLETS.values())
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(k) for k in watched]
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    return {'error': None, 'delta': [lamports(k) - b for k, b in zip(watched, before)],
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def fixed_cases():
    cases = []
    add = lambda *entries, **k: cases.append(case(*entries, **k))
    # Ordinary payouts, duplicates and zero amounts.
    add((0, 1000))
    add((0, 1000), (1, 2000), (2, 3))
    add((0, 1000), (0, 2000))
    add((0, 0), (1, 5))
    add((0, 0), lamports=0)
    add((0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1))
    for lamports in (0, 500, FLOOR - 1, FLOOR, 10**9):
        add(lamports=lamports)
    # The PDA must end at zero or at the zero-length rent floor or above.
    for left in (0, 1, FLOOR - 1, FLOOR, FLOOR + 1):
        add((0, 10**6), lamports=10**6 + left)
        add((0, 4 * 10**5), (1, 6 * 10**5), lamports=10**6 + left)
    add((0, 1000), lamports=FLOOR - 1)
    # Insufficient balance, at any position, before the floor check.
    add((0, 10**9 + 1))
    add((0, 1000), (1, 10**9))
    add((0, 10**9), (1, 1))
    add((0, MAX))
    add((0, 1), (1, MAX))
    add((0, 1000), lamports=0)
    # Paying the PDA itself moves nothing but still counts in the total.
    add(('r', 1000), lamports=891_000)
    add(('r', 1000), lamports=1000)
    add(('r', 1001), lamports=1000)
    add(('r', 0), (0, 1000))
    add(('r', 10**9), (0, 10**9))
    # Read-only wallets fail only when they would receive lamports.
    add((8, 1000))
    add((8, 0), (0, 1000))
    add((0, 10**9 + 1), (8, 1000))
    add((8, 1000), (0, 10**9 + 1))
    add((8, 10**9 + 1))
    add((8, 1000), lamports=500)
    # The is_holder_reward_enabled flag is not consulted.
    add((0, 1000), enabled=False)
    add(lamports=500, enabled=False)
    # Exactly two remaining accounts per amount.
    for n in (0, 1, 2):
        entries = [(i, 1000) for i in range(n)]
        for accounts in {0, 1, 2 * n - 1, 2 * n + 1, 2 * n + 2} - {2 * n, -1}:
            add(*entries, accounts=accounts)
    # Token quotes: an empty list succeeds; anything else needs a token account.
    add(quote='token')
    add(quote='token', lamports=500)
    add(quote='token', lamports=0)
    add((0, 0), quote='token')
    add((0, 1000), quote='token')
    add((0, 1000), quote='token', accounts=1)
    # Account checks and their order.
    add((0, 1000), quote='missing')
    add((0, 1000), signed=False)
    add((0, 1000), authority_ok=False)
    add((0, 1000), address_ok=False)
    add((0, 1000), signed=False, quote='missing', authority_ok=False)
    add((0, 1000), quote='missing', authority_ok=False)
    add((0, 1000), authority_ok=False, address_ok=False)
    add((0, 1000), address_ok=False, accounts=1)
    add((0, 1000), authority_ok=False, accounts=1)
    add((0, 1000), quote='missing', accounts=1)
    return cases


def random_cases(count=120, seed=1891):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        lamports = rng.choice((0, 500, FLOOR, 10**6, 10**9, rng.randrange(1, 2 * 10**6)))
        entries = []
        for _ in range(rng.randrange(0, 7)):
            payee = rng.choice(tuple(range(8)) * 3 + ('r', 8, 9))
            amount = rng.choice((0, 1, 1000, rng.randrange(1, max(2, lamports)), rng.randrange(1, 10**6), MAX))
            entries.append((payee, amount))
        accounts = 2 * len(entries) + rng.choice((0,) * 12 + (-1, 1, 2))
        cases.append(case(*entries, lamports=lamports, accounts=max(0, accounts),
                          quote=rng.choice(('native',) * 12 + ('token', 'missing')),
                          signed=rng.random() > 0.06, authority_ok=rng.random() > 0.06,
                          address_ok=rng.random() > 0.06, enabled=rng.random() > 0.3))
    return cases


class HolderDistributionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'holder-distribution-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if answer == 'escalation':
            self.assertIn('PrivilegeEscalation', str(captured['error']))
            return
        self.assertIsNone(captured['error'])
        _, final, recipients, total, credits = answer.split(',')
        credits = {} if credits == '-' else {int(k): int(v) for k, v in (p.split(':') for p in credits.split('+'))}
        # Signed deltas: the PDA, the claim authority, then wallets 0-9.
        expected = [int(final) - item['lamports'], 0] + [credits.get(i, 0) for i in range(10)]
        self.assertEqual(captured['delta'], expected)
        # On the SOL path the event reports the zero key as quote_mint, not wrapped SOL.
        quote = bytes(STABLE) if item['quote'] == 'token' else bytes(32)
        event = (EVENT_DISC + struct.pack('<q', NOW) + bytes(MINT) + quote
                 + struct.pack('<QQ', int(recipients), int(total)))
        self.assertEqual(captured['events'], [event])

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once a payout is
        # reversed, the reported total moves, or the PDA balance is off by one.
        samples = (case((0, 1000), (1, 2000)), case(('r', 1000), (0, 5), lamports=891_000), case((0, 10**6),
                   lamports=10**6))
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            _, final, recipients, total, credits = answer.split(',')
            for text in (f'ok,{int(final) + 1},{recipients},{total},{credits}',
                         f'ok,{final},{recipients},{int(total) + 1},{credits}',
                         f'ok,{final},{int(recipients) + 1},{total},{credits}'):
                with self.subTest(case=host_line(item), tampered=text):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)
            flipped = dict(captured, delta=[-d for d in captured['delta']])
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, flipped)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers} - {'ok'}, {
            'error:1', 'error:2006', 'error:3010', 'error:3012', 'error:6000', 'error:6085', 'error:6086',
            'error:6087', 'escalation'})
        finals = [a.split(',') for a in answers if a.startswith('ok,')]
        self.assertTrue(any(f[1] == '0' for f in finals))
        self.assertTrue(any(f[1] == str(FLOOR) for f in finals))
        self.assertTrue(any(f[4] == '-' and f[3] != '0' for f in finals))


if __name__ == '__main__':
    unittest.main()
