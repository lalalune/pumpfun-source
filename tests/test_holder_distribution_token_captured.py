"""Captured-program checks for holder payouts that use a source token account.

Every case runs Pump `distribute_fee_to_holders` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs from `evidence/dependencies/`. Cases
pass `holder_rewards_token_account` (the holder-rewards PDA's ATA): SPL Token
and Token-2022 quotes paid out of it, with recipient ATAs created on demand,
and a wrapped-SOL source closed into the PDA before lamport payouts. The same
inputs go to `programs/pump/recovered/holder_distribution_token_host.rs`. The
error, the signed lamport deltas (PDA, claim authority, wallets), the signed
token deltas (source, recipient ATAs), which ATAs were created and the full
`DistributeFeeToHoldersEvent` bytes must agree. This shows matching behaviour
on these inputs only; it is not a byte-identity claim.
`tests/test_holder_distribution_captured.py` covers the SOL path without a
source account, and `scripts/pump_holder_distribution_differential.py`
compares candidate builds with the captured program; this is a deterministic
model of the source-account paths.
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
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN_2022_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN_2022_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/holder_distribution_token_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN_2022 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
PROGRAMS = {'t': TOKEN, 't22': TOKEN_2022}
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
STABLE = Pubkey.from_bytes(bytes([41]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([42]) * 32)
MINT = Pubkey.from_bytes(bytes([31]) * 32)
IX = next(i for i in IDL['instructions'] if i['name'] == 'distribute_fee_to_holders')
GLOBAL_DISC = next(bytes(a['discriminator']) for a in IDL['accounts'] if a['name'] == 'Global')
EVENT_DISC = next(bytes(e['discriminator']) for e in IDL['events'] if e['name'] == 'DistributeFeeToHoldersEvent')

PAYER = Keypair.from_seed(bytes([201]) * 32)
AUTHORITY = Keypair.from_seed(bytes([202]) * 32)
ELSEWHERE = Pubkey.from_bytes(bytes([99]) * 32)
WALLETS = {i: Pubkey.from_bytes(bytes([70 + i]) * 32) for i in range(10)}
READONLY = (8, 9)
GLOBAL = Pubkey.find_program_address([b'global'], PUMP)[0]
REWARDS = Pubkey.find_program_address([b'holder-rewards', bytes(MINT)], PUMP)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
NOW = 1_700_000_000
TOKEN_RENT = 2_039_280
WALLET_LAMPORTS = 890_880
FLOOR = 890_880
MAX = 2**64 - 1


def ata(wallet, mint, program):
    return Pubkey.find_program_address([bytes(wallet), bytes(program), bytes(mint)], ATA_PROGRAM)[0]


def mint_data():
    data = bytearray(82)
    data[44] = 6
    data[45] = 1
    return bytes(data)


def token_account(mint, owner, amount, native=False):
    data = bytearray(165)
    data[0:32] = bytes(mint)
    data[32:64] = bytes(owner)
    data[64:72] = struct.pack('<Q', amount)
    data[108] = 1
    if native:
        data[109:113] = struct.pack('<I', 1)
        data[113:121] = struct.pack('<Q', TOKEN_RENT)
    return bytes(data)


def case(*entries, **changes):
    item = dict(signed=True, authority_ok=True, native=False, program='t', mint_program=None,
                source='111:1000000', lamports=10**9, accounts=None, entries=tuple(entries))
    item.update(changes)
    # One ATA per wallet: a later entry sees the state the first one set up.
    first = {}
    for payee, _, state in item['entries']:
        if state != 'x':
            first.setdefault(payee, state)
    item['entries'] = tuple((p, a, s if s == 'x' else first[p]) for p, a, s in item['entries'])
    if item['mint_program'] is None:
        item['mint_program'] = item['program']
    if item['accounts'] is None:
        item['accounts'] = 2 * len(item['entries'])
    return item


def payee_text(payee):
    if payee == 'r':
        return 'r'
    return f'{"ro" if payee in READONLY else "w"}{payee}'


def host_line(item):
    entries = '+'.join(f'{payee_text(p)}:{a}:{s}' for p, a, s in item['entries']) or '-'
    return ','.join(map(str, (int(item['signed']), int(item['authority_ok']), int(item['native']), item['program'],
                              item['mint_program'], item['source'], item['lamports'], item['accounts'], entries)))


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(TOKEN_2022, TOKEN_2022_ELF)
    vm.add_program_from_file(ATA_PROGRAM, ATA_ELF)
    vm.set_clock(Clock(100, NOW, 0, 0, NOW))
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(AUTHORITY.pubkey(), Account(10**10, b'', SYSTEM))
    global_data = bytearray(1088)
    global_data[:8] = GLOBAL_DISC
    global_data[8] = 1
    global_data[1054:1086] = bytes(AUTHORITY.pubkey() if item['authority_ok'] else ELSEWHERE)
    global_data[1086] = 1
    vm.set_account(GLOBAL, Account(10**9, bytes(global_data), PUMP))
    vm.set_account(MINT, Account(1_461_600, mint_data(), TOKEN))
    program = PROGRAMS[item['program']]
    mint = WSOL if item['native'] else STABLE
    vm.set_account(mint, Account(1_461_600, mint_data(), PROGRAMS[item['mint_program']]))
    if item['lamports']:
        vm.set_account(REWARDS, Account(item['lamports'], b'', SYSTEM))
    for wallet in WALLETS.values():
        vm.set_account(wallet, Account(WALLET_LAMPORTS, b'', SYSTEM))
    source = ata(REWARDS, mint, program)
    if item['source'] != '-':
        flags, amount = item['source'].split(':')
        owner = REWARDS if flags[0] == '1' else ELSEWHERE
        held = mint if flags[1] == '1' else OTHER_MINT
        owning = program if flags[2] == '1' else (TOKEN_2022 if program == TOKEN else TOKEN)
        lamports = TOKEN_RENT + (int(amount) if item['native'] else 0)
        vm.set_account(source, Account(lamports, token_account(held, owner, int(amount), item['native']), owning))
    names = {'global': GLOBAL, 'holder_reward_claim_authority': AUTHORITY.pubkey(), 'mint': MINT,
             'holder_rewards': REWARDS, 'holder_rewards_token_account': source if item['source'] != '-' else PUMP,
             'quote_mint': mint, 'quote_token_program': program, 'associated_token_program': ATA_PROGRAM,
             'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = [AccountMeta(names[a['name']], a.get('signer', False) and item['signed'], a.get('writable', False))
             for a in IX['accounts']]
    remaining = []
    for payee, _, state in item['entries']:
        wallet = REWARDS if payee == 'r' else WALLETS[payee]
        target = ata(wallet, mint, program)
        if state == 'e' and payee != 'r':
            vm.set_account(target, Account(TOKEN_RENT, token_account(mint, wallet, 0), program))
        if state == 'x':
            target = ata(wallet, OTHER_MINT, program)
        remaining += [AccountMeta(wallet, False, payee not in READONLY), AccountMeta(target, False, True)]
    remaining += [AccountMeta(ELSEWHERE, False, True)] * max(0, item['accounts'] - len(remaining))
    metas += remaining[:item['accounts']]
    data = (bytes(IX['discriminator']) + len(item['entries']).to_bytes(4, 'little')
            + b''.join(struct.pack('<Q', amount) for _, amount, _ in item['entries']))
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)], PAYER.pubkey(),
        [PAYER] + ([AUTHORITY] if item['signed'] else []), vm.latest_blockhash())
    lamport_keys = [REWARDS, AUTHORITY.pubkey()] + list(WALLETS.values())
    token_keys = [source] + [ata(w, mint, program) for w in WALLETS.values()]

    def lamports(key):
        account = vm.get_account(key)
        return account.lamports if account else 0

    def tokens(key):
        account = vm.get_account(key)
        if account is None or len(account.data) < 165 or account.lamports == 0:
            return None
        return struct.unpack('<Q', bytes(account.data)[64:72])[0]

    before = [lamports(k) for k in lamport_keys], [tokens(k) for k in token_keys]
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    after = [lamports(k) for k in lamport_keys], [tokens(k) for k in token_keys]
    return {'error': None, 'lamports': [a - b for a, b in zip(after[0], before[0])],
            'tokens_before': before[1], 'tokens_after': after[1],
            'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def fixed_cases():
    cases = []
    add = lambda *entries, **k: cases.append(case(*entries, **k))
    for program in ('t', 't22'):
        # Payouts into new and existing ATAs, duplicates, zero amounts.
        add((0, 1000, 'n'), program=program)
        add((0, 1000, 'e'), program=program)
        add((0, 1000, 'n'), (1, 2000, 'e'), (2, 3, 'n'), program=program)
        add((0, 1000, 'n'), (0, 2000, 'n'), program=program)
        add((0, 0, 'n'), (1, 0, 'e'), program=program)
        add((0, 10**6, 'e'), program=program)
        add(program=program)
        add(program=program, source='-')
        # Insufficient balance at any position; earlier ATA rent is undone.
        add((0, 10**6 + 1, 'n'), program=program)
        add((0, 600_000, 'n'), (1, 600_000, 'n'), program=program)
        add((0, MAX, 'e'), program=program)
        # Paying the PDA is a self-transfer that still checks the balance.
        add(('r', 1000, 'e'), program=program)
        add(('r', 10**6 + 1, 'e'), program=program)
        add(('r', MAX, 'e'), ('r', 1, 'e'), source='111:' + str(MAX), program=program)
        add(('r', MAX, 'e'), (0, 0, 'n'), source='111:' + str(MAX), program=program)
        # Read-only wallets are fine: only the ATA is written.
        add((8, 1000, 'n'), program=program)
        add((8, 1000, 'e'), (9, 0, 'n'), program=program)
        # Recipient account checks.
        add((0, 1000, 'x'), program=program)
        add((0, 1000, 'n'), (1, 1000, 'x'), program=program)
        add((0, 0, 'x'), program=program)
        add((0, 1000, 'n'), program=program, source='-')
        add((0, 0, 'n'), program=program, source='-')
        add((0, 1000, 'x'), program=program, source='-')
        add((0, 1000, 'n'), program=program, accounts=1)
        add((0, 1000, 'n'), program=program, accounts=3)
        # Source constraints and their order.
        for flags in ('011', '101', '110', '001', '100', '000', '010'):
            add((0, 1000, 'n'), program=program, source=flags + ':1000000')
        add(program=program, source='110:1000000')
        add((0, 1000, 'n'), program=program, source='011:1000000', signed=False)
        add((0, 1000, 'n'), program=program, source='011:1000000', authority_ok=False)
        add((0, 1000, 'n'), program=program, source='011:1000000', accounts=1)
    # A mint owned by the other token program.
    add((0, 1000, 'n'), mint_program='t22')
    add((0, 1000, 'e'), mint_program='t22')
    add((0, 0, 'n'), mint_program='t22')
    add(mint_program='t22')
    add((0, 1000, 'n'), program='t22', mint_program='t')
    add((0, 1000, 'e'), program='t22', mint_program='t')
    add((0, 0, 'e'), program='t22', mint_program='t')
    add(('r', 5, 'e'), program='t22', mint_program='t')
    # Wrapped-SOL source: closed into the PDA, then lamport payouts.
    for amount in (0, 5000, 10**6):
        add(native=True, source=f'111:{amount}', lamports=0)
        add((0, 1000, 'e'), native=True, source=f'111:{amount}', lamports=0)
        add((0, 1000, 'e'), (1, 2000, 'e'), native=True, source=f'111:{amount}', lamports=10**6)
    add((0, TOKEN_RENT + 5000, 'e'), native=True, source='111:5000', lamports=0)
    add((0, TOKEN_RENT + 5001, 'e'), native=True, source='111:5000', lamports=0)
    add((0, TOKEN_RENT + 5000 - FLOOR, 'e'), native=True, source='111:5000', lamports=0)
    add((0, TOKEN_RENT + 5001 - FLOOR, 'e'), native=True, source='111:5000', lamports=0)
    add((0, 1000, 'x'), native=True, source='111:5000', lamports=10**6)
    add((8, 1000, 'e'), native=True, source='111:5000', lamports=10**6)
    add((8, 0, 'e'), (0, 1, 'e'), native=True, source='111:5000', lamports=10**6)
    add(('r', 10**6, 'e'), native=True, source='111:5000', lamports=0)
    add(('r', MAX, 'e'), ('r', 1, 'e'), native=True, source='111:5000', lamports=MAX - TOKEN_RENT - 5000)
    add((0, 1000, 'e'), native=True, source='-', lamports=10**6)
    for flags in ('011', '101', '110'):
        add((0, 1000, 'e'), native=True, source=flags + ':5000', lamports=10**6)
    return cases


def random_cases(count=120, seed=2026):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        native = rng.random() < 0.25
        program = 't' if native else rng.choice(('t', 't22'))
        amount = rng.choice((0, 1000, 10**6, rng.randrange(1, 10**7)))
        source = '-' if rng.random() < 0.08 else ''.join(rng.choice('1111111110') for _ in range(3)) + f':{amount}'
        entries = []
        for _ in range(rng.randrange(0, 6)):
            payee = rng.choice(tuple(range(8)) * 3 + ('r', 8, 9))
            value = rng.choice((0, 1, 1000, rng.randrange(1, max(2, amount)), rng.randrange(1, 10**6), MAX))
            entries.append((payee, value, rng.choice('nnneeex')))
        accounts = max(0, 2 * len(entries) + rng.choice((0,) * 12 + (-1, 1)))
        mint_program = program if native or rng.random() < 0.9 else ('t22' if program == 't' else 't')
        cases.append(case(*entries, native=native, program=program, mint_program=mint_program, source=source,
                          lamports=rng.choice((0, FLOOR, 10**6, 10**9)), accounts=accounts,
                          signed=rng.random() > 0.05, authority_ok=rng.random() > 0.05))
    return cases


class HolderDistributionTokenCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'holder-distribution-token-host'
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
        if answer == 'incorrect-program-id':
            self.assertIn('IncorrectProgramId', str(captured['error']))
            return
        self.assertIsNone(captured['error'])
        _, final, paid, source, recipients, total, credits, created = answer.split(',')
        credits = {} if credits == '-' else {int(k): int(v) for k, v in (p.split(':') for p in credits.split('+'))}
        created = set() if created == '-' else {int(k) for k in created.split('+')}
        # Signed lamport deltas: the PDA, the claim authority, then wallets 0-9.
        lamport_credits = credits if item['native'] else {}
        self.assertEqual(captured['lamports'], [int(final) - item['lamports'], -int(paid)]
                         + [lamport_credits.get(i, 0) for i in range(10)])
        before, after = captured['tokens_before'], captured['tokens_after']
        if item['native']:
            # The wrapped-SOL source is closed (or was never there).
            self.assertIsNone(after[0])
            self.assertEqual(after[1:], before[1:])
        else:
            self.assertEqual(after[0], None if source == '-' else int(source))
            if source != '-':
                self.assertEqual(after[0] - before[0], int(source) - int(item['source'].split(':')[1]))
            token_credits = {} if item['native'] else credits
            for i in range(10):
                if i in created:
                    self.assertIsNone(before[1 + i])
                    self.assertEqual(after[1 + i], token_credits.get(i, 0))
                elif before[1 + i] is None:
                    self.assertIsNone(after[1 + i])
                    self.assertNotIn(i, token_credits)
                else:
                    self.assertEqual(after[1 + i] - before[1 + i], token_credits.get(i, 0))
        quote = bytes(32) if item['native'] else bytes(STABLE)
        event = (EVENT_DISC + struct.pack('<q', NOW) + bytes(MINT) + quote
                 + struct.pack('<QQ', int(recipients), int(total)))
        self.assertEqual(captured['events'], [event])

    def run_cases(self, cases):
        for item, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_programs(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_programs(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: passing captured runs must fail once the PDA
        # balance, the ATA rent, the source balance, the total, a payout or
        # the created set moves.
        samples = (case((0, 1000, 'n'), (1, 2000, 'e')), case((0, 1000, 'n'), program='t22'),
                   case((0, 1000, 'e'), native=True, source='111:5000', lamports=10**6))
        for item, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(item)
            self.assert_matches(item, answer, captured)
            fields = answer.split(',')
            tampered = []
            for index, change in ((1, 1), (2, 1), (3, -1), (5, 1)):
                if fields[index] != '-':
                    changed = list(fields)
                    changed[index] = str(int(changed[index]) + change)
                    tampered.append(','.join(changed))
            changed = list(fields)
            changed[6] = fields[6].replace('0:1000', '0:999')
            tampered.append(','.join(changed))
            if not item['native']:
                changed = list(fields)
                changed[7] = '-'
                tampered.append(','.join(changed))
            for text in tampered:
                with self.subTest(case=host_line(item), tampered=text):
                    with self.assertRaises(AssertionError):
                        self.assert_matches(item, text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a.split(',')[0] for a in answers} - {'ok'}, {
            'error:1', 'error:2014', 'error:2015', 'error:2021', 'error:3010', 'error:6000', 'error:6024',
            'error:6085', 'error:6086', 'error:6087', 'escalation', 'incorrect-program-id'})
        oks = [a.split(',') for a in answers if a.startswith('ok,')]
        self.assertTrue(any(o[2] == '2074080' for o in oks))
        self.assertTrue(any(o[2] == '2039280' for o in oks))


if __name__ == '__main__':
    unittest.main()
