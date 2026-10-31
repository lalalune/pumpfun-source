"""Captured-program checks for v3 trades with one key in two account slots.

Every case runs Pump `sell_v3`, `buy_v3` or `buy_exact_quote_in_v3` from the
captured `evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL
Token, Token-2022 and Associated Token programs, where
`Global.buyback_fee_recipient` names the buyer, the curve, a mint, `global`,
`fee_config`, a program, the event authority or a token account of the trade,
or where the buyer passes the curve's token account as their own. The pricing
comes from the hosts of `tests/test_v3_trade_accounting_captured.py` and
`tests/test_v3_exact_quote_captured.py`; `programs/pump/recovered/v3_alias_host.rs`
then says what the shared key changes. The error, each key's lamports and
tokens, the stored reserves and the TradeEvent must agree. This shows matching
behavior on these inputs only; it is not a byte-identity claim.
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v3_exact_quote_captured as exact
import test_v3_trade_accounting_captured as base

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_alias_host.rs'

USER = base.USER.pubkey()
QUOTES = ('sol', 'wsol', 'spl', 't22')
ROLES = ('buyback', 'user', 'curve', 'base', 'quote', 'fee', 'global', 'ea', 'pump', 'token', 'zero', 'user_base',
         'curve_base', 'user_quote', 'curve_quote', 'uva')
MODEL_ROLE = {'user': 'user', 'curve': 'curve', 'ea': 'ea', 'pump': 'pump', 'zero': 'zero'}
START = 10**12


def role_key(role, r):
    return {'buyback': base.BUYBACK, 'user': USER, 'curve': base.CURVE, 'base': base.BASE, 'quote': r['quote_mint'],
            'fee': base.FEE_CONFIG, 'global': base.GLOBAL, 'ea': base.EVENT_AUTHORITY, 'pump': base.PUMP,
            'token': base.TOKEN, 'zero': base.SYSTEM, 'user_base': r['user_base'], 'curve_base': r['curve_base'],
            'user_quote': r['user_quote'], 'curve_quote': r['curve_quote'], 'uva': base.USER_VOLUME}[role]


def item(role, kind, quote, base_slot=False, quote_slot=False, **over):
    return dict(role=role, kind=kind, quote=quote, base_slot=base_slot, quote_slot=quote_slot, over=over)


def trade_case(it):
    """The case dict the base fixtures and hosts read."""
    over = dict(it['over'], quote=it['quote'])
    amount = over.pop('amount', 10**9 if it['kind'] == 'exact' else 10**12)
    limit = over.pop('limit', None)
    if it['kind'] == 'exact':
        return dict(exact.default_case(spendable=amount, min_tokens=1 if limit is None else limit, **over),
                    user_base=10**13, buy=1, amount=amount, limit=1 if limit is None else limit)
    buy = int(it['kind'] == 'buy')
    return base.default_case(buy=buy, amount=amount, limit=(10**12 if buy else 0) if limit is None else limit, **over)


def baselines(items):
    answers = [None] * len(items)
    for model, kinds in ((base.model, ('sell', 'buy')), (exact.model, ('exact',))):
        chosen = [i for i, it in enumerate(items) if it['kind'] in kinds]
        for i, answer in zip(chosen, model([trade_case(items[i]) for i in chosen]) if chosen else []):
            answers[i] = answer
    return answers


class Vm:
    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((base.PUMP, base.PUMP_ELF), (base.TOKEN, base.TOKEN_ELF), (base.TOKEN22, base.TOKEN22_ELF),
                          (base.ATA, base.ATA_ELF)):
            self.vm.add_program_from_file(key, path)
        self.vm.set_clock(Clock(100, base.TIMESTAMP, base.EPOCH, base.EPOCH, base.TIMESTAMP))
        self.stale = {}

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def tokens(self, key):
        account = self.vm.get_account(key)
        return base.token_amount(bytes(account.data)) if account and len(account.data) >= 72 else 0

    def stale_keys(self, quote):
        if quote not in self.stale:
            r = base.roles(base.default_case(quote=quote))
            keys = {r['user_quote'], r['curve_quote'], base.ata(base.BUYBACK, r['quote_mint'], r['program'])}
            keys |= {base.ata(role_key(role, r), r['quote_mint'], r['program']) for role in ROLES}
            self.stale[quote] = keys
        return self.stale[quote]

    def run(self, it):
        vm = self.vm
        c = trade_case(it)
        r = base.roles(c)
        key = role_key(it['role'], r)
        native = r['native']
        recipient = key if native else base.ata(key, r['quote_mint'], r['program'])
        data = bytearray(base.global_bytes(c))
        data[741:773] = bytes(key)
        for stale in self.stale_keys(it['quote']):
            vm.set_account(stale, Account(0, b'', base.SYSTEM))
        vm.set_account(base.GLOBAL, Account(10**9, bytes(data), base.PUMP))
        vm.set_account(base.FEE_CONFIG, Account(10**9, base.fee_config_bytes(c), base.FEES))
        vm.set_account(USER, Account(START, b'', base.SYSTEM))
        vm.set_account(base.BUYBACK, Account(10**9, b'', base.SYSTEM))
        vm.set_account(base.BASE, Account(10**9, base.mint_bytes(c['mint_supply'], 6), base.TOKEN))
        vm.set_account(r['quote_mint'], Account(10**9, base.mint_bytes(10**18, 9 if native else 6), r['program']))
        vm.set_account(base.CURVE, Account(c['curve_lamports'], base.curve_bytes(c, r['curve_field']), base.PUMP))
        vm.set_account(r['curve_base'], Account(base.TOKEN_RENT, base.token_bytes(base.BASE, base.CURVE, c['curve_base']), base.TOKEN))
        vm.set_account(r['user_base'], Account(base.TOKEN_RENT, base.token_bytes(base.BASE, USER, c['user_base']), base.TOKEN))
        if not native:
            vm.set_account(recipient, Account(base.TOKEN_RENT, base.token_bytes(r['quote_mint'], key, 0), r['program']))
            held = min(base.U64, c['rqr'] + c['creator_fee'] + c['protocol_fees'])
            vm.set_account(r['curve_quote'], Account(base.TOKEN_RENT, base.token_bytes(r['quote_mint'], base.CURVE, held), r['program']))
            vm.set_account(r['user_quote'], Account(base.TOKEN_RENT, base.token_bytes(r['quote_mint'], USER, c['user_quote']), r['program']))
        uva = bytearray(137)
        uva[:8] = base.ACCOUNT_DISC['UserVolumeAccumulator']
        uva[8:40] = bytes(USER)
        vm.set_account(base.USER_VOLUME, Account(base.rent(137), bytes(uva), base.PUMP))
        names = {'global': base.GLOBAL, 'base_mint': base.BASE, 'quote_mint': r['quote_mint'],
                 'base_token_program': base.TOKEN, 'quote_token_program': r['program'], 'bonding_curve': base.CURVE,
                 'associated_base_bonding_curve': r['curve_base'], 'associated_quote_bonding_curve': r['curve_quote'],
                 'user': USER, 'associated_base_user': r['curve_base'] if it['base_slot'] else r['user_base'],
                 'associated_quote_user': r['curve_quote'] if it['quote_slot'] else r['user_quote'],
                 'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG,
                 'buyback_fee_recipient': recipient, 'system_program': base.SYSTEM,
                 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP}
        ix = base.IX[{'sell': 'sell_v3', 'buy': 'buy_v3', 'exact': 'buy_exact_quote_in_v3'}[it['kind']]]
        metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
        payload = bytes(ix['discriminator']) + struct.pack('<QQ', c['amount'], c['limit'])
        if it['kind'] != 'sell':
            payload += bytes([c['partial']])
        watched = (USER, base.CURVE, key)
        tokens = (r['user_base'], r['curve_base'], r['user_quote'], r['curve_quote'], recipient)
        before = [self.lamports(k) for k in watched], [self.tokens(k) for k in tokens]
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), Instruction(base.PUMP, payload, metas)], USER, [base.USER],
            vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            names = re.search(r'UnbalancedInstruction', text)
            return {'error': int(code.group(1)) if code else names.group() if names else text}
        stored = vm.get_account(base.CURVE)
        return {'error': None, 'lamports': [self.lamports(k) - b for k, b in zip(watched, before[0])],
                'tokens': [self.tokens(k) - b for k, b in zip(tokens, before[1])], 'roles': r, 'recipient': recipient,
                'reserves': struct.unpack_from('<4Q', stored.data, 8), 'case': c,
                'events': [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]}


def baseline_text(answer):
    kind, m = answer
    if kind == 'error':
        return f'error:{m}'
    return ':'.join(str(m[k]) for k in ('user_quote', 'curve_quote', 'buyback_recipient', 'rent_top_up', 'base_moved'))


def host_line(it, answer):
    native = it['quote'] == 'sol'
    return ','.join(map(str, (MODEL_ROLE.get(it['role'], 'ordinary'), int(native), int(it['kind'] == 'sell'),
                              int(it['base_slot']), int(it['quote_slot']), baseline_text(answer))))


def fixed_cases():
    cases = []
    for quote in QUOTES:
        for kind in ('sell', 'buy', 'exact'):
            for role in ROLES:
                cases.append(item(role, kind, quote))
                cases.append(item(role, kind, quote, buyback_bps=0))
                cases.append(item(role, kind, quote, buyback_bps=1))
                cases.append(item(role, kind, quote, amount=1))
                cases.append(item(role, kind, quote, complete=1))
                cases.append(item(role, kind, quote, cashback=1))
                cases.append(item(role, kind, quote, cashback=1, quote_slot=quote != 'sol', base_slot=True))
                cases.append(item(role, kind, quote, limit=2**63))
                cases.append(item(role, kind, quote, base_slot=True))
                cases.append(item(role, kind, quote, base_slot=True, complete=1))
                cases.append(item(role, kind, quote, curve_lamports=base.rent(166) + (5 * 10**9 if quote == 'sol' else 0) - 1_000))
                if quote != 'sol':
                    cases.append(item(role, kind, quote, quote_slot=True))
                    cases.append(item(role, kind, quote, quote_slot=True, complete=1))
                    cases.append(item(role, kind, quote, quote_slot=True, base_slot=True))
    return cases


def random_cases(count=600, seed=4417):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        quote = rng.choice(QUOTES)
        kind = rng.choice(('sell', 'buy', 'exact'))
        cases.append(item(rng.choice(ROLES), kind, quote, base_slot=rng.random() < 0.1,
                          quote_slot=quote != 'sol' and rng.random() < 0.05,
                          buyback_bps=rng.choice((0, 1, 500, 5_000, 10_000)), amount=rng.randrange(1, 10**(9 if kind == 'exact' else 12)),
                          cashback=int(rng.random() < 0.2), mayhem=int(rng.random() < 0.2),
                          creator_fee=rng.choice((0, 10**6)), protocol_fees=rng.choice((0, 10**6))))
    return cases


class V3AliasCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in {**ELF_SHA256, **exact.ELF_SHA256}.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'v3-alias-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.vm = Vm()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, cases):
        priced = baselines(cases)
        text = ''.join(host_line(it, p) + '\n' for it, p in zip(cases, priced))
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        return list(zip(out, priced))

    def assert_matches(self, it, pair, captured):
        answer, (kind, m) = pair
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        if not answer.startswith('ok'):
            self.assertEqual(captured['error'], answer)
            return
        self.assertIsNone(captured['error'])
        values = list(map(int, answer.split(',')[1:]))
        user, curve, recipient = values[:3]
        if it['role'] not in ('user', 'curve'):
            self.assertEqual(captured['lamports'][2], recipient)
        self.assertEqual(captured['lamports'][:2], [user - base.TX_FEE, curve])
        self.assertEqual(captured['tokens'][:2], values[3:5])
        if it['quote'] != 'sol':
            self.assertEqual(captured['tokens'][2:4], values[5:7])
            if it['role'] not in ('user', 'curve'):
                self.assertEqual(captured['tokens'][4], values[7])
        self.assertEqual(captured['reserves'], (m['vtr'], m['vqr'], m['rtr'], m['rqr']))
        expected = base.trade_event(captured['case'], captured['roles'], m)
        if it['kind'] == 'exact':
            expected = expected.replace(struct.pack('<I', 3) + b'buy', struct.pack('<I', 18) + b'buy_exact_quote_in')
        self.assertEqual(captured['events'][0], expected)

    def run_cases(self, cases):
        pairs = self.answers(cases)
        self.assertEqual(len(pairs), len(cases))
        for it, pair in zip(cases, pairs):
            with self.subTest(case=str(it), host=pair[0]):
                self.assert_matches(it, pair, self.vm.run(it))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_changed_answers(self):
        # Negative control: a passing captured trade must fail once a balance changes.
        it = item('user', 'buy', 'sol')
        (answer, priced), = self.answers([it])
        captured = self.vm.run(it)
        self.assert_matches(it, (answer, priced), captured)
        fields = answer.split(',')
        for index in (1, 2, 4, 5):
            changed = ','.join(str(int(f) + 1) if i == index else f for i, f in enumerate(fields))
            with self.subTest(index=index), self.assertRaises(AssertionError):
                self.assert_matches(it, (changed, priced), captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a, _ in self.answers(fixed_cases())}
        self.assertLessEqual({'ok', 'UnbalancedInstruction', 'error:4', 'error:2000', 'error:6005', 'error:6010', 'error:6062', 'error:6094'}, outcomes)


if __name__ == '__main__':
    unittest.main()
