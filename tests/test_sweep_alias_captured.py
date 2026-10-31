"""Captured-program checks for a fee recipient that shares a key with another slot.

Every case runs Pump `sweep_protocol_fee` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token
and Associated Token programs, where `Global.fee_recipient` or
`Global.reserved_fee_recipient` names the payer, the curve, `global`, a mint, a
program, the event authority or a token account of the call. The same inputs
go to `programs/pump/recovered/sweep_alias_host.rs`, and the error, the
lamports of each key, the token balances, the stored buckets and the
SweepBondingCurveFeeEvent amount must agree. Account fixtures come from
`tests/test_sweep_fees_captured.py`. This shows matching behavior on these
inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_sweep_fees_captured as base

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/sweep_alias_host.rs'

PAYER = base.PAYER.pubkey()
ROLES = {'payer': PAYER, 'curve': base.CURVE, 'global': base.GLOBAL, 'base': base.BASE_MINT, 'quote': base.QUOTE_MINT,
         'wsol': base.NATIVE_MINT, 'ea': base.EVENT_AUTHORITY, 'token': base.TOKEN, 'ata_program': base.ATA,
         'pump': base.PUMP, 'wallet': base.FEE_RECIPIENT, 'zero': base.SYSTEM,
         'curve_ata': base.ata(base.CURVE, base.QUOTE_MINT), 'vault': base.VAULT}
# Keys whose balance the fixture sets for the recipient.
OWN_BALANCE = ('wallet', 'ea', 'vault')
FIXED = {'payer': 10**12, 'curve': None, 'global': 10**9, 'base': 10**9, 'quote': 10**9, 'wsol': 10**9,
         'curve_ata': base.TOKEN_RENT}
RENT = base.CURVE_RENT


def case(role, **changes):
    item = dict(role=role, native=True, mayhem=False, wrong_quote=False, real_quote=5 * 10**9, creator_fee=3_000_000,
                protocol_fees=7_000_000, curve_extra=RENT, recipient_lamports=10**9, curve_ata=10**10,
                recipient_ata=True)
    item.update(changes)
    return item


def curve_lamports(item):
    reserved = item['real_quote'] + item['creator_fee'] + item['protocol_fees'] if item['native'] else 0
    return reserved + item['curve_extra']


class Vm:
    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(base.PUMP, base.PUMP_ELF)
        self.vm.add_program_from_file(base.TOKEN, base.TOKEN_ELF)
        self.vm.add_program_from_file(base.ATA, base.ATA_ELF)
        self.vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
        self.stale = {base.ata(key, base.QUOTE_MINT) for key in ROLES.values()}
        self.stale |= {base.ata(key, base.NATIVE_MINT) for key in ROLES.values()}

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def tokens(self, key):
        account = self.vm.get_account(key)
        return struct.unpack_from('<Q', bytes(account.data), 64)[0] if account and len(account.data) >= 72 else None

    def run(self, item):
        vm = self.vm
        role = item['role']
        key = ROLES[role]
        fields = dict(real_quote=item['real_quote'], mayhem=item['mayhem'], native=item['native'],
                      creator_fee=item['creator_fee'], protocol_fees=item['protocol_fees'])
        data = bytearray(base.global_data())
        data[483 if item['mayhem'] else 41:515 if item['mayhem'] else 73] = bytes(key)
        for stale in self.stale:
            vm.set_account(stale, Account(0, b'', base.SYSTEM))
        vm.set_account(PAYER, Account(10**12, b'', base.SYSTEM))
        vm.set_account(base.GLOBAL, Account(10**9, bytes(data), base.PUMP))
        vm.set_account(base.BASE_MINT, Account(10**9, base.mint_data(), base.TOKEN))
        vm.set_account(base.NATIVE_MINT, Account(10**9, base.mint_data(9), base.TOKEN))
        vm.set_account(base.QUOTE_MINT, Account(10**9, base.mint_data(), base.TOKEN))
        vm.set_account(base.OTHER, Account(10**9, base.mint_data(), base.TOKEN))
        vm.set_account(base.CURVE, Account(curve_lamports(item), base.curve_data(fields), base.PUMP))
        if role in OWN_BALANCE:
            vm.set_account(key, Account(item['recipient_lamports'], b'', base.SYSTEM))
        quote = base.NATIVE_MINT if item['native'] else base.QUOTE_MINT
        passed = base.OTHER if item['wrong_quote'] else quote
        curve_ata, recipient_ata = base.ata(base.CURVE, passed), base.ata(key, passed)
        if not item['native']:
            vm.set_account(curve_ata, Account(base.TOKEN_RENT, base.token_data(passed, base.CURVE, item['curve_ata']), base.TOKEN))
            if item['recipient_ata'] and recipient_ata != curve_ata:
                vm.set_account(recipient_ata, Account(base.TOKEN_RENT, base.token_data(passed, key, 0), base.TOKEN))
        names = {'payer': PAYER, 'global': base.GLOBAL, 'base_mint': base.BASE_MINT, 'quote_mint': passed,
                 'quote_token_program': base.TOKEN, 'associated_token_program': base.ATA, 'system_program': base.SYSTEM,
                 'bonding_curve': base.CURVE, 'associated_quote_bonding_curve': curve_ata, 'recipient': key,
                 'associated_quote_recipient': recipient_ata, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        ix = base.IX['sweep_protocol_fee']
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([Instruction(base.PUMP, bytes(ix['discriminator']), metas)], PAYER,
                                               [base.PAYER], vm.latest_blockhash())
        before = self.lamports(key)
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            names = re.search(r'UnbalancedInstruction|ArithmeticOverflow|InsufficientFundsForRent', text)
            return {'error': int(code.group(1)) if code else names.group() if names else text}
        stored = vm.get_account(base.CURVE)
        events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
        return {'error': None, 'payer': self.lamports(PAYER), 'curve': self.lamports(base.CURVE),
                'recipient': self.lamports(key), 'before': before, 'bucket': struct.unpack_from('<Q', stored.data, 133)[0],
                'source_tokens': self.tokens(curve_ata), 'target_tokens': self.tokens(recipient_ata), 'events': events}


def recipient_held(item):
    return item['recipient_lamports'] if item['role'] in OWN_BALANCE else 10**9


def host_line(item):
    role = item['role']
    name = role if role in ('payer', 'curve', 'ea', 'pump', 'zero') else 'ordinary'
    fields = [name, int(item['native']), int(item['mayhem']), int(item['wrong_quote']), item['real_quote'],
              item['creator_fee'], item['protocol_fees'], curve_lamports(item), recipient_held(item), item['curve_ata'],
              int(item['recipient_ata'])]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda role, **k: cases.append(case(role, **k))
    for role in ROLES:
        for native in (True, False):
            for mayhem in (False, True):
                common = dict(native=native, mayhem=mayhem)
                add(role, **common)
                add(role, protocol_fees=0, **common)
                add(role, protocol_fees=1, **common)
                add(role, wrong_quote=True, **common)
                add(role, recipient_ata=False, **common)
                add(role, recipient_ata=False, protocol_fees=0, **common)
                for extra in (1, RENT - 1, RENT, RENT + 1, 10**9):
                    add(role, curve_extra=extra, **common)
        # A native curve short of the SOL it owes; the top-up fills the gap.
        for extra in (-7_000_000, -7_000_000 + 1, -RENT - 7_000_000 + 7_000_000, -RENT, -RENT - 1, -1):
            add(role, curve_extra=extra)
        add(role, real_quote=0, creator_fee=0, protocol_fees=7_000_000, curve_extra=-7_000_000 + RENT - 1)
        add(role, real_quote=0, creator_fee=0, protocol_fees=RENT, curve_extra=-RENT)
        add(role, real_quote=0, creator_fee=0, protocol_fees=RENT, curve_extra=-1)
        # Curves that start below rent, around the runtime's end-state rule.
        for extra in (-2, -1, -RENT + 1):
            add(role, real_quote=0, creator_fee=0, protocol_fees=RENT, curve_extra=extra)
            add(role, real_quote=0, creator_fee=0, protocol_fees=RENT + 1, curve_extra=extra)
            add(role, real_quote=0, creator_fee=0, protocol_fees=RENT - 1, curve_extra=extra)
        add(role, native=False, curve_ata=6_999_999)
        add(role, native=False, curve_ata=7_000_000)
        for lamports in (0, 1, base.ZERO_RENT, 10**9):
            add(role, recipient_lamports=lamports, protocol_fees=base.ZERO_RENT + 1)
    # A curve with no lamports does not exist.
    return [item for item in cases if curve_lamports(item) > 0]


def random_cases(count=500, seed=7121):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        pf = rng.choice((0, rng.randrange(1, 10**6), rng.randrange(1, 10**10)))
        cases.append(case(rng.choice(tuple(ROLES)), native=rng.random() < 0.6, mayhem=rng.random() < 0.3,
                          real_quote=rng.randrange(0, 10**10), creator_fee=rng.choice((0, rng.randrange(0, 10**8))),
                          protocol_fees=pf, curve_extra=rng.choice((1, RENT, rng.randrange(1, 3 * RENT))),
                          recipient_lamports=10**9, curve_ata=rng.choice((pf, pf + 1, 10**12)),
                          recipient_ata=rng.random() < 0.6))
    return cases


class SweepAliasCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'sweep-alias-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.vm = Vm()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if not answer.startswith('ok'):
            self.assertEqual(captured['error'], answer)
            return
        self.assertIsNone(captured['error'])
        amount, spends, gets, curve, recipient, tokens, bucket = map(int, answer.split(',')[1:])
        self.assertEqual(captured['payer'], 10**12 - base.TX_FEE - spends + gets)
        self.assertEqual(captured['curve'], curve)
        self.assertEqual(captured['bucket'], bucket)
        if item['role'] not in ('payer', 'curve'):
            self.assertEqual(captured['recipient'] - captured['before'], recipient - recipient_held(item))
        if not item['native']:
            self.assertEqual(captured['source_tokens'], item['curve_ata'] - tokens)
            if item['role'] != 'curve' and (tokens or item['recipient_ata']):
                self.assertEqual(captured['target_tokens'], tokens)
        self.assertEqual(len(captured['events']), int(amount > 0))
        if amount:
            self.assertEqual(struct.unpack_from('<Q', captured['events'][0], len(captured['events'][0]) - 9)[0], amount)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.vm.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_changed_answers(self):
        # Negative control: a passing captured sweep to the payer must fail
        # once a lamport figure or the event amount changes.
        item = case('payer', curve_extra=0)
        answer = self.host_answers([item])[0]
        captured = self.vm.run(item)
        self.assert_matches(item, answer, captured)
        fields = answer.split(',')
        for index in (1, 2, 3, 4):
            changed = ','.join(str(int(f) + 1) if i == index else f for i, f in enumerate(fields))
            with self.subTest(index=index), self.assertRaises(AssertionError):
                self.assert_matches(item, changed, captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'ArithmeticOverflow', 'InsufficientFundsForRent', 'UnbalancedInstruction',
                                    'error:1', 'error:2000', 'error:6000', 'error:6004'})


if __name__ == '__main__':
    unittest.main()
