"""Captured-program checks for Pump SOL trades with one key in two slots.

Every case runs Pump `buy`, `buy_exact_sol_in`, `sell`, `buy_v2`,
`buy_exact_quote_in_v2` or `sell_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, against a Global whose fee and
buyback recipients name the buyer, the curve, the vault, each other, a program
or another account of the instruction. The same inputs go to
`programs/pump/recovered/trade_alias_host.rs`, and the error, the net lamports
of each key, tokens, stored curve and TradeEvent fields must agree. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import itertools
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_buy_v2_captured as base

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ELF_SHA256 = {
    base.PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    base.FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    base.TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    base.ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/trade_alias_host.rs'

USER, TOKEN, WSOL, PUMP, CURVE = base.USER, base.TOKEN, base.WSOL, base.PUMP, base.CURVE
BUYER = USER.pubkey()
CURVE_V2 = base.pda(b'bonding-curve-v2', bytes(base.MINT))[0]
BUYER_ATA, CURVE_ATA = base.ata(BUYER), base.ata(CURVE)
PARTIES = {
    'fee': base.FEE_RECIPIENT, 'buyback': base.BUYBACK, 'user': BUYER, 'curve': CURVE, 'vault': base.VAULT,
    'uata': BUYER_ATA, 'cata': CURVE_ATA, 'uva': base.USER_VOLUME, 'gva': base.GLOBAL_VOLUME, 'global': base.GLOBAL,
    'mint': base.MINT, 'config': base.FEE_CONFIG, 'cv2': CURVE_V2, 'sharing': base.SHARING, 'wsol': WSOL,
    'token': TOKEN, 'pump': PUMP, 'ea': base.EVENT_AUTHORITY,
}
OPS = {'buy': 'buy', 'exact': 'buy_exact_sol_in', 'sell': 'sell', 'buy2': 'buy_v2',
       'exact2': 'buy_exact_quote_in_v2', 'sell2': 'sell_v2'}
BUYS = ('buy', 'exact', 'buy2', 'exact2')
SELLS = ('sell', 'sell2')
LEGACY = ('buy', 'exact', 'sell')
USER_TOKENS = 10**13
BUY_RESERVES = (base.VT, base.VS, base.RT, 0)
SELL_RESERVES = (873_000_000_000_000, 36_872_852_233, 593_100_000_000_000, 6_872_852_233)
DEFAULT_ARGS = {'buy': (10**9, 10**13), 'exact': (10**9, 1), 'sell': (10**12, 0),
                'buy2': (10**9, 10**13), 'exact2': (10**9, 1), 'sell2': (10**12, 0)}
TIERS = ((0, 95, 30),)
FIELD = re.compile(r'Fieldless\((\w+)\)')


def case(op, fee='fee', buyback='buyback', **changes):
    item = dict(op=op, fee=fee, buyback=buyback, bps=5000, vault=0, user=base.USER_LAMPORTS, args=DEFAULT_ARGS[op],
                tiers=TIERS, complete=False, curve_ata=False, quote_user=None,
                reserves=SELL_RESERVES if op in SELLS else BUY_RESERVES)
    item.update(changes)
    return item


def host_line(item, mode='trade'):
    tokens = USER_TOKENS if item['op'] in SELLS else 0
    fields = [mode, item['op'], *item['reserves'], base.SUPPLY, int(item['complete']),
              ';'.join(f'{t}:{p}:{c}' for t, p, c in item['tiers']), item['bps'], item['vault'], item['user'],
              tokens, item['reserves'][2], *item['args'], item['fee'], item['buyback'], int(item['curve_ata'])]
    return ','.join(str(f) for f in fields)


class Harness:
    """One VM: reloading the four programs per case would take half a second each."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, base.PUMP_ELF)
        self.vm.add_program_from_file(base.FEES, base.FEES_ELF)
        self.vm.add_program_from_file(TOKEN, base.TOKEN_ELF)
        self.vm.add_program_from_file(base.ATA, base.ATA_ELF)
        self.vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
        self.stale = {base.FEE_RECIPIENT, base.BUYBACK, base.VAULT}

    def install(self, item):
        vt, vs, rt, rs = item['reserves']
        sells = item['op'] in SELLS
        fee, buyback = PARTIES[item['fee']], PARTIES[item['buyback']]
        stored = bytearray(base.global_data(item['bps'], False))
        stored[41:73] = bytes(fee)
        stored[741:773] = bytes(buyback)
        curve = base.curve_data(dict(vt=vt, vs=vs, rt=rt, rs=rs, supply=base.SUPPLY, complete=item['complete'],
                                     creator=True, creator_bps=0))
        accounts = {
            BUYER: Account(item['user'], b'', base.SYSTEM),
            base.GLOBAL: Account(10**9, bytes(stored), PUMP),
            base.MINT: Account(10**9, base.mint_data(base.SUPPLY), TOKEN),
            WSOL: Account(10**9, base.mint_data(0, 9), TOKEN),
            CURVE: Account(base.CURVE_RENT + rs, curve, PUMP),
            CURVE_ATA: Account(base.TOKEN_RENT, base.token_data(CURVE, rt), TOKEN),
            BUYER_ATA: Account(base.TOKEN_RENT, base.token_data(BUYER, USER_TOKENS if sells else 0), TOKEN),
            base.FEE_CONFIG: Account(10**9, base.fee_config_data(item['tiers']), base.FEES),
            base.GLOBAL_VOLUME: Account(10**9, base.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
            base.USER_VOLUME: Account(10**9, base.ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(BUYER) + bytes(97), PUMP),
            CURVE_V2: Account(10**7, b'', base.SYSTEM),
        }
        if item['vault']:
            accounts[base.VAULT] = Account(item['vault'], b'', base.SYSTEM)
        for key in self.stale - set(accounts):
            self.vm.set_account(key, Account(0, b'', base.SYSTEM))
        for key, account in accounts.items():
            self.vm.set_account(key, account)
        self.stale = set(accounts) | {base.FEE_RECIPIENT, base.BUYBACK, base.VAULT}
        return fee, buyback

    def metas(self, item, fee, buyback):
        ix = base.IX[OPS[item['op']]]
        names = {
            'global': base.GLOBAL, 'base_mint': base.MINT, 'mint': base.MINT, 'quote_mint': WSOL,
            'base_token_program': TOKEN, 'token_program': TOKEN, 'quote_token_program': TOKEN,
            'associated_token_program': base.ATA, 'fee_recipient': fee,
            'associated_quote_fee_recipient': base.ata(fee, WSOL), 'buyback_fee_recipient': buyback,
            'associated_quote_buyback_fee_recipient': base.ata(buyback, WSOL), 'bonding_curve': CURVE,
            'associated_base_bonding_curve': CURVE_ATA, 'associated_bonding_curve': CURVE_ATA,
            'associated_quote_bonding_curve': base.ata(CURVE, WSOL), 'user': BUYER,
            'associated_base_user': CURVE_ATA if item['curve_ata'] else BUYER_ATA,
            'associated_user': CURVE_ATA if item['curve_ata'] else BUYER_ATA,
            'associated_quote_user': item['quote_user'] or base.ata(BUYER, WSOL), 'creator_vault': base.VAULT,
            'associated_creator_vault': base.ata(base.VAULT, WSOL), 'sharing_config': base.SHARING,
            'global_volume_accumulator': base.GLOBAL_VOLUME, 'user_volume_accumulator': base.USER_VOLUME,
            'associated_user_volume_accumulator': base.ata(base.USER_VOLUME, WSOL), 'fee_config': base.FEE_CONFIG,
            'fee_program': base.FEES, 'system_program': base.SYSTEM, 'event_authority': base.EVENT_AUTHORITY,
            'program': PUMP,
        }
        metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
        if item['op'] in LEGACY:
            metas += [AccountMeta(CURVE_V2, False, False), AccountMeta(buyback, False, True)]
        return ix, metas

    def run(self, item):
        fee, buyback = self.install(item)
        ix, metas = self.metas(item, fee, buyback)
        lamports = lambda key: self.vm.get_account(key).lamports if self.vm.get_account(key) else 0
        watched = set(PARTIES.values())
        before = {key: lamports(key) for key in watched}
        data = bytes(ix['discriminator']) + struct.pack('<QQ', *item['args'])
        self.vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], BUYER, [USER], self.vm.latest_blockhash())
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text) or FIELD.search(text)
            return {'error': int(code.group(1)) if code and code.group(1).isdigit() else (code.group(1) if code else text)}
        delta = {key: lamports(key) - value for key, value in before.items() if lamports(key) != value}
        events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
        trade = base.decode_trade(next(e for e in events if e[:8] == base.TRADE_EVENT))
        stored = self.vm.get_account(CURVE).data
        tokens = lambda key: struct.unpack_from('<Q', self.vm.get_account(key).data, 64)[0]
        return {'error': None, 'delta': delta, 'events': len(events), 'trade': trade,
                'reserves': struct.unpack_from('<QQQQ', stored, 8), 'complete': stored[48],
                'tokens': (tokens(BUYER_ATA), tokens(CURVE_ATA))}


def check(item, answer, captured):
    """The first difference, or None."""
    if answer == 'panic':
        return None if 'ProgramFailedToComplete' in str(captured['error']) else f'not a panic: {captured}'
    if answer.startswith('error:'):
        want = answer[6:]
        return None if str(captured['error']) == want else f'wanted {want}, got {captured}'
    if captured['error'] is not None:
        return f'wanted success, got {captured}'
    f = answer.split(',')
    delta = {}
    for pair in filter(None, f[1].split(';')):
        name, amount = pair.split('=')
        delta[PARTIES[name]] = int(amount)
    n = list(map(int, f[2:]))
    wanted = dict(delta=delta, tokens=tuple(n[:2]), reserves=tuple(n[2:6]), complete=n[6], events=2 if n[6] else 1)
    for key, value in wanted.items():
        if captured[key] != value:
            return f'{key}: wanted {value}, got {captured[key]}'
    t = captured['trade']
    got = (t['sol_amount'], t['token_amount'], t['fee'], t['creator_fee'], t['buyback_fee'], t['buyback_bps'])
    return None if got == tuple(n[7:13]) else f'event: wanted {n[7:13]}, got {got}'


def matrix_cases():
    """Every recipient pair on all six trades, with the buyback at 0, half and all of the fee."""
    return [case(op, fee, buyback, bps=bps) for op, fee, buyback, bps in
            itertools.product(OPS, PARTIES, PARTIES, (0, 5000, 10000))]


def stop_cases():
    """Stops that come first whatever the keys are, and the curve's token account as the buyer's."""
    cases = []
    for op, (fee, buyback) in itertools.product(OPS, (('fee', 'buyback'), ('user', 'user'), ('curve', 'vault'),
                                                      ('pump', 'buyback'), ('fee', 'pump'), ('token', 'ea'))):
        cases.append(case(op, fee, buyback, complete=True))
        cases.append(case(op, fee, buyback, args=(0, 0)))
        cases.append(case(op, fee, buyback, tiers=((0, 2 * 10**4, 30),), args=(10**9, 10**3)))
        cases.append(case(op, fee, buyback, args=(base.RT + 10**15, 2**64 - 1)))
        cases.append(case(op, fee, buyback, curve_ata=True))
        cases.append(case(op, fee, buyback, curve_ata=True, args=(0, 0)))
        cases.append(case(op, fee, buyback, curve_ata=True, complete=True))
    for op in BUYS:
        cases.append(case(op, curve_ata=True, args=(base.RT, 10**13)))
    cases.append(case('buy', curve_ata=True, reserves=(1000, 10**9, 900, 0), args=(900, 10**12)))
    cases.append(case('buy2', curve_ata=True, reserves=(1000, 10**9, 900, 0), args=(900, 10**12)))
    return cases


def vault_cases():
    """The vault's rent top-up reads its balance before any recipient is paid."""
    cases = []
    for op, vault, (fee, buyback) in itertools.product(OPS, (0, 1, 890_000, 890_879, 890_880, 10**9),
                                                       (('fee', 'buyback'), ('vault', 'buyback'), ('fee', 'vault'),
                                                        ('vault', 'vault'), ('buyback', 'buyback'), ('user', 'vault'))):
        cases.append(case(op, fee, buyback, vault=vault))
    return cases


def quote_user_cases():
    """The v2 `associated_quote_user` slot is never read on the SOL path."""
    return [case(op, quote_user=key) for op in ('buy2', 'exact2', 'sell2') for key in PARTIES.values()
            if key not in (PUMP,)]


def order_inputs(count=120, seed=7362):
    rng = random.Random(seed)
    items = []
    for _ in range(count):
        op = rng.choice(BUYS)
        args = (10**rng.randrange(9, 13), 10**16) if op in ('buy', 'buy2') else (10**rng.randrange(9, 11), 1)
        fee, buyback = rng.choice((('user', 'buyback'), ('fee', 'user'), ('user', 'user'), ('vault', 'user'),
                                   ('user', 'curve'), ('curve', 'user'), ('user', 'vault'), ('fee', 'buyback')))
        items.append(case(op, fee, buyback, args=args, bps=rng.choice((0, 1000, 2500, 5000, 7500, 9000, 10000)),
                          vault=rng.choice((0, 890_880)),
                          tiers=((0, rng.choice((100, 1000, 5000, 9000)), rng.choice((0, 100, 3000, 20000))),)))
    return items


def random_cases(count=700, seed=7363):
    rng = random.Random(seed)
    cases = []
    parties = list(PARTIES)
    for _ in range(count):
        op = rng.choice(list(OPS))
        vt = rng.choice((base.VT, rng.randrange(10**8, 10**16)))
        rt = rng.randrange(1, vt)
        vs = rng.randrange(10**7, 10**12)
        rs = rng.randrange(0, vs + 1) if op in SELLS else 0
        amount = rng.randrange(1, 10**rng.randrange(4, 14))
        args = (amount, rng.choice((0, 1))) if op in SELLS else (amount, 2**63) if op in ('buy', 'buy2') else (amount, 1)
        cases.append(case(op, rng.choice(parties), rng.choice(parties), reserves=(vt, vs, rt, rs), args=args,
                          bps=rng.choice((0, rng.randrange(0, 10_001))), vault=rng.choice((0, 1, 890_880)),
                          complete=rng.random() < 0.03, curve_ata=rng.random() < 0.08,
                          tiers=((0, rng.randrange(0, 3000), rng.randrange(0, 3000)),)))
    return cases


class TradeAliasCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'trade-alias-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.harness = Harness()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, lines):
        text = ''.join(line + '\n' for line in lines)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def run_cases(self, cases):
        answers = self.host_answers(host_line(item) for item in cases)
        self.assertEqual(len(answers), len(cases))
        failures = []
        for item, answer in zip(cases, answers):
            difference = check(item, answer, self.harness.run(item))
            if difference:
                failures.append(f'{host_line(item)} -> {answer}: {difference}')
        self.assertEqual(len(failures), 0, '\n'.join(failures[:12]))
        return answers

    def test_recipient_matrix_matches_captured_program(self):
        answers = self.run_cases(matrix_cases())
        stops = {a for a in answers if a.startswith('error:')}
        self.assertEqual(stops, {'error:2000', 'error:ExternalAccountLamportSpend', 'error:PrivilegeEscalation',
                                 'error:ReadonlyLamportChange', 'error:UnbalancedInstruction'})

    def test_fixed_stops_match_captured_program(self):
        stops = {a.split(',')[0] for a in self.run_cases(stop_cases())}
        self.assertLessEqual({'error:2000', 'error:4', 'error:6005', 'error:6020', 'error:6021', 'error:6022', 'ok'}, stops)

    def test_vault_rent_matches_captured_program(self):
        self.run_cases(vault_cases())

    def test_unread_quote_slot_matches_captured_program(self):
        self.run_cases(quote_user_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_smallest_buyer_balance_shows_the_payment_order(self):
        # A transfer from the buyer to the buyer moves nothing but needs the
        # balance, so the smallest balance that works depends on the order.
        inputs = order_inputs()
        needs = self.host_answers(host_line(item, 'need') for item in inputs)
        cases = []
        for item, need in zip(inputs, needs):
            if need == 'none':
                continue
            for balance in (int(need), int(need) - 1):
                # Under this floor the payer fails ahead of the program.
                if balance >= 895_880:
                    cases.append(dict(item, user=balance))
        self.assertGreater(len(cases), 150)
        answers = self.run_cases(cases)
        self.assertGreater(sum(a == 'error:1' for a in answers), 60)

    def test_unknown_trade_op_is_rejected(self):
        # A misspelt op must stop the driver instead of running another trade.
        fields = host_line(case('buy')).split(',')
        for op in ('sel', 'exact22', 'sell3', 'BUY'):
            line = ','.join([op if i == 1 else f for i, f in enumerate(fields)])
            result = subprocess.run([str(self.host)], input=line + '\n', capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, op)
            self.assertEqual(result.stdout, '', op)
            self.assertIn(f'unknown op {op}', result.stderr, op)

    def test_checker_rejects_a_changed_movement(self):
        # Negative control: moving one lamport between two keys must be caught.
        item = case('buy', 'user', 'vault')
        answer = self.host_answers([host_line(item)])[0]
        captured = self.harness.run(item)
        self.assertIsNone(check(item, answer, captured))
        for key in (CURVE, base.VAULT, BUYER):
            changed = dict(captured['delta'])
            changed[key] += 1
            self.assertIsNotNone(check(item, answer, dict(captured, delta=changed)))


if __name__ == '__main__':
    unittest.main()
