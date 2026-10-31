"""Captured-program checks for several trade instructions in one transaction.

`test_same_tx_captured.py` joins the legacy instructions into one
transaction but runs no trade: the v2 and v3 trades, the token quotes and
Token-2022 are outside its fixture, and its default budget is never
exceeded, so the budget formula and the order of a budget and a trace
failure inside one step stay unconfirmed there. Here each case runs the
same trade steps twice on the captured `evidence/original/pump/deployed.so`
(with the captured Pump Fees, SPL Token, Token-2022 and ATA programs): one
transaction per step on one chain, then all steps in one transaction on a
fresh chain. The separate run gives each step's outcome, compute units
and trace entries to `programs/pump/recovered/same_tx_trades_host.rs`,
which answers how the joined transaction ends. The joined run must agree
on the error and its instruction index, the fee, the units, the trace and
the events, and must end on the separate runs' state (plus the saved
fees) or, on a failure, on the start state less the fee. This shows
matching behaviour on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
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
from solders.message import Message
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_v2_token_quote_captured as q  # noqa: E402
import test_v3_trade_accounting_captured as t3  # noqa: E402

HOST_SOURCE = q.ROOT / 'programs/pump/recovered/same_tx_trades_host.rs'
USER = q.USER.pubkey()
MAX_LIMIT = 1_400_000
SEPARATE_LIMIT = MAX_LIMIT
LEAD_UNITS = 150
TF = (0, 0, 0, 250, 10**18)
MISSING4 = ('vault', 'uva', 'recipient', 'buyback')

BUY2 = ('buy_v2', 10**12, 10**15, 0)
SELL2 = ('sell_v2', 10**11, 0)
EXACT2 = ('exact_v2', 10**9, 1, 0)
BUY3 = ('buy_v3', 10**12, 10**15, 0)
SELL3 = ('sell_v3', 10**11, 0)
EXACT3 = ('exact_v3', 10**9, 1, 0)
TOO_MANY2 = ('sell_v2', 10**13 + 1, 0)
TOO_MANY3 = ('sell_v3', 10**13 + 1, 0)
PAY = ('pay', 1_000)


def case(ops, limit=MAX_LIMIT, **setup):
    return dict(ops=ops, limit=limit, setup=setup)


VM = []
TOUCHED = set()


def shared_vm():
    """One VM per run: loading five programs per case takes most of the time."""
    if not VM:
        vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        for key, path in ((q.PUMP, q.PUMP_ELF), (q.FEES, q.FEES_ELF), (q.TOKEN, q.TOKEN_ELF),
                          (q.TOKEN22, q.TOKEN22_ELF), (q.ATA, q.ATA_ELF)):
            vm.add_program_from_file(key, path)
        VM.append(vm)
    vm = VM[0]
    for key in TOUCHED:
        account = vm.get_account(key)
        if account is not None and not account.executable and 'Sysvar1111' not in str(account.owner):
            vm.set_account(key, Account(0, b'', q.SYSTEM))
    TOUCHED.clear()
    return vm


class Chain:
    """The trade fixture of `test_v2_token_quote_captured` (its `Global`,
    fee config and curve bytes also satisfy the v3 handlers: the fields
    only they read start at the same values), so one chain carries both
    generations of trade. `quote='sol'` is the v3 handlers' native path;
    v2 steps need a token quote."""

    def __init__(self, quote='spl', tf=None, missing=(), **over):
        self.vm = shared_vm()
        self.vm.set_clock(Clock(100, q.TIMESTAMP, q.EPOCH, q.EPOCH, q.TIMESTAMP))
        c = q.default_case(**dict(over, quote=quote, tf=tf))
        self.c, self.quote = c, quote
        native = quote == 'sol'
        if native:
            r = dict(quote_mint=q.WSOL, program=q.TOKEN, recipient=q.BUYBACK, vault=None, buyback_quote=None,
                     user_quote=q.ata(USER, q.WSOL), curve_quote=q.ata(q.CURVE, q.WSOL),
                     user_base=q.ata(USER, q.BASE), curve_base=q.ata(q.CURVE, q.BASE))
        else:
            r = q.roles(c)
        self.r = r
        accounts = {
            q.GLOBAL: Account(10**9, q.global_bytes(c), q.PUMP),
            q.FEE_CONFIG: Account(10**9, q.fee_config_bytes(c), q.FEES),
            q.GLOBAL_VOLUME: Account(10**9, q.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), q.PUMP),
            USER: Account(10**15, b'', q.SYSTEM),
            q.BUYBACK: Account(10**9, b'', q.SYSTEM),
            q.BASE: Account(10**9, q.mint_bytes(c['mint_supply'], 6), q.TOKEN),
            q.CURVE: Account(c['curve_lamports'] + (c['rqr'] if native else 0),
                             q.curve_bytes(c, q.SYSTEM if native else r['quote_mint']), q.PUMP),
            r['curve_base']: Account(q.TOKEN_RENT, q.token_bytes(q.BASE, q.CURVE, c['curve_base']), q.TOKEN),
            r['user_base']: Account(q.TOKEN_RENT, q.token_bytes(q.BASE, USER, c['user_base']), q.TOKEN),
        }
        if native:
            accounts[q.WSOL] = Account(10**9, q.mint_bytes(10**18, 9), q.TOKEN)
        else:
            accounts[r['quote_mint']] = Account(10**9, q.mint_bytes(10**18, r['decimals'], tf), r['program'])
            ext = tf is not None
            held = {'curve': (r['curve_quote'], q.CURVE, c['curve_quote']), 'user': (r['user_quote'], USER, c['user_quote']),
                    'vault': (r['vault_quote'], r['vault'], 0), 'uva': (r['uva_quote'], q.USER_VOLUME, 0),
                    'recipient': (r['recipient_quote'], r['recipient'], 0), 'buyback': (r['buyback_quote'], q.BUYBACK, 0)}
            for name, (key, owner, amount) in held.items():
                if name not in missing:
                    accounts[key] = Account(q.TOKEN_RENT, q.token_bytes(r['quote_mint'], owner, amount, ext), r['program'])
        uva = bytearray(137)
        uva[:8] = q.ACCOUNT_DISC['UserVolumeAccumulator']
        uva[8:40] = bytes(USER)
        accounts[q.USER_VOLUME] = Account(q.rent(137), bytes(uva), q.PUMP)
        for key, account in accounts.items():
            self.vm.set_account(key, account)
        TOUCHED.update(accounts)
        self.snap_keys = sorted({USER, q.GLOBAL, q.FEE_CONFIG, q.GLOBAL_VOLUME, q.USER_VOLUME, q.BASE,
                                 r['quote_mint'], q.CURVE, q.BUYBACK, q.FEE_RECIPIENT, q.RESERVED, q.SHARING,
                                 r['curve_base'], r['user_base'], r['curve_quote'], r['user_quote'],
                                 *[k for k in (r.get('vault'), r.get('vault_quote'), r.get('uva_quote'),
                                               r.get('recipient_quote'), r.get('buyback_quote')) if k is not None]},
                                key=bytes)

    def ix(self, op):
        r = self.r
        if op[0] == 'pay':
            return transfer(TransferParams(from_pubkey=USER, to_pubkey=q.BUYBACK, lamports=op[1]))
        if op[0].endswith('_v2'):
            names = {
                'global': q.GLOBAL, 'base_mint': q.BASE, 'quote_mint': r['quote_mint'], 'base_token_program': q.TOKEN,
                'quote_token_program': r['program'], 'associated_token_program': q.ATA, 'fee_recipient': r['recipient'],
                'associated_quote_fee_recipient': q.ata(r['recipient'], r['quote_mint'], r['program']),
                'buyback_fee_recipient': q.BUYBACK,
                'associated_quote_buyback_fee_recipient': q.ata(q.BUYBACK, r['quote_mint'], r['program']),
                'bonding_curve': q.CURVE, 'associated_base_bonding_curve': r['curve_base'],
                'associated_quote_bonding_curve': r['curve_quote'], 'user': USER,
                'associated_base_user': r['user_base'], 'associated_quote_user': r['user_quote'],
                'creator_vault': r['vault'], 'associated_creator_vault': r['vault_quote'],
                'sharing_config': q.SHARING, 'global_volume_accumulator': q.GLOBAL_VOLUME,
                'user_volume_accumulator': q.USER_VOLUME, 'associated_user_volume_accumulator': r['uva_quote'],
                'fee_config': q.FEE_CONFIG, 'fee_program': q.FEES, 'system_program': q.SYSTEM,
                'event_authority': q.EVENT_AUTHORITY, 'program': q.PUMP,
            }
            kind = {'buy_v2': 'buy', 'sell_v2': 'sell', 'exact_v2': 'exact'}[op[0]]
            spec = q.IX[q.IX_NAME[kind]]
            data = bytes(spec['discriminator']) + struct.pack('<QQ', op[1], op[2])
            if kind != 'sell':
                data += bytes([op[3] if len(op) > 3 else 0])
            return Instruction(q.PUMP, data, [AccountMeta(names[a['name']], bool(a.get('signer')),
                                                          bool(a.get('writable'))) for a in spec['accounts']])
        names = {
            'global': q.GLOBAL, 'base_mint': q.BASE, 'quote_mint': r['quote_mint'], 'base_token_program': q.TOKEN,
            'quote_token_program': r['program'], 'bonding_curve': q.CURVE,
            'associated_base_bonding_curve': r['curve_base'], 'associated_quote_bonding_curve': r['curve_quote'],
            'user': USER, 'associated_base_user': r['user_base'], 'associated_quote_user': r['user_quote'],
            'user_volume_accumulator': q.USER_VOLUME, 'fee_config': q.FEE_CONFIG,
            'buyback_fee_recipient': q.BUYBACK if self.quote == 'sol' else r['buyback_quote'],
            'system_program': q.SYSTEM, 'event_authority': q.EVENT_AUTHORITY, 'program': q.PUMP,
        }
        spec = q.IX[{'buy_v3': 'buy_v3', 'sell_v3': 'sell_v3', 'exact_v3': 'buy_exact_quote_in_v3'}[op[0]]]
        data = bytes(spec['discriminator']) + struct.pack('<QQ', op[1], op[2])
        if op[0] != 'sell_v3':
            data += bytes([op[3] if len(op) > 3 else 0])
        return Instruction(q.PUMP, data, [AccountMeta(names[a['name']], bool(a.get('signer')),
                                                      bool(a.get('writable'))) for a in spec['accounts']])

    def send(self, ops, limit=MAX_LIMIT):
        self.vm.expire_blockhash()
        bh = self.vm.latest_blockhash()
        pre = [] if limit is None else [set_compute_unit_limit(limit)]
        instructions = [self.ix(o) for o in ops]
        TOUCHED.update(meta.pubkey for ix in instructions for meta in ix.accounts)
        msg = Message.new_with_blockhash(pre + instructions, USER, bh)
        tx = Transaction.new_unsigned(msg)
        tx.partial_sign([q.USER], bh)
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        groups = json.loads(meta.to_json())['inner_instructions'] or []
        return dict(err=str(result.err()) if failed else None, cu=meta.compute_units_consumed(),
                    trace=len(pre) + len(ops) + sum(len(g) for g in groups), logs=meta.logs())

    def snap(self):
        out = {}
        for key in self.snap_keys:
            a = self.vm.get_account(key)
            out[str(key)] = None if a is None or a.lamports == 0 else (a.lamports, str(a.owner), bytes(a.data))
        return out


def label(err):
    if err is None:
        return 'ok'
    custom = re.search(r'Custom\((\d+)\)', err)
    if custom:
        return f'c{custom.group(1)}'
    if 'MaxInstructionTraceLengthExceeded' in err:
        return 'trace'
    if 'ComputationalBudgetExceeded' in err or 'ProgramFailedToComplete' in err:
        return 'budget'
    return re.sub(r'\W', '', err)


def events(logs):
    return [line for line in logs if line.startswith('Program data: ')]


def step_line(op, alone):
    units, trace = alone['cu'] - LEAD_UNITS, alone['trace'] - 1
    return ':'.join(map(str, (label(alone['err']), units, trace, units, int(op[0] == 'pay'))))


def run_case(item):
    """Run the steps one transaction each, then together, on two fresh chains."""
    apart = Chain(**item['setup'])
    before = apart.snap()
    steps, emitted = [], []
    for op in item['ops']:
        alone = apart.send([op], SEPARATE_LIMIT)
        steps.append(step_line(op, alone))
        if alone['err']:
            break
        emitted += events(alone['logs'])
    final = apart.snap()
    together = Chain(**item['setup'])
    limit = '-' if item['limit'] is None else item['limit']
    builtins = sum(op[0] == 'pay' for op in item['ops'])
    declared = f'{limit},{len(item["ops"]) - builtins},{builtins}'
    return dict(line=';'.join([declared, *steps]), before=before, apart=final, emitted=emitted,
                joined=together.send(item['ops'], item['limit']), after=together.snap())


def fixed_cases():
    cases = []
    for quote, tf in (('spl', None), ('wsol', None), ('usdc', None), ('t22', None), ('t22', TF)):
        setup = dict(quote=quote, tf=tf)
        cases += [
            case([BUY2, SELL2], **setup), case([SELL2, BUY2], **setup), case([BUY2, BUY2, SELL2], **setup),
            case([EXACT2, SELL2], **setup), case([BUY3, SELL3], **setup), case([SELL3, BUY3], **setup),
            case([EXACT3, SELL3], **setup), case([SELL3, BUY2], **setup), case([BUY2, SELL3], **setup),
            case([BUY3, SELL2, EXACT3], **setup), case([PAY, BUY2, SELL3], **setup),
            # Rollback: a later failure undoes the earlier steps.
            case([BUY2, TOO_MANY2], **setup), case([TOO_MANY3], **setup), case([BUY3, BUY2, TOO_MANY3], **setup),
            case([SELL2, BUY2, ('sell_v2', 10**11, 10**15)], **setup),
        ]
    # The native quote carries v3 steps only.
    cases += [
        case([BUY3, SELL3], quote='sol'), case([SELL3, BUY3, EXACT3], quote='sol'),
        case([BUY3, TOO_MANY3], quote='sol'), case([PAY, BUY3, SELL3], quote='sol'),
    ]
    # A trade that completes the curve, then another trade on it.
    cases += [
        case([BUY2, SELL2], quote='spl', rtr=10**12), case([BUY2, BUY3], quote='spl', rtr=10**12),
        case([BUY3, SELL3], quote='t22', tf=TF, rtr=10**12),
    ]
    # The first trade creates the four quote ATAs the later steps reuse.
    for quote, tf in (('spl', None), ('t22', TF)):
        setup = dict(quote=quote, tf=tf, missing=MISSING4)
        cases += [case([BUY2, SELL2], **setup), case([SELL2, BUY2], **setup), case([BUY2, BUY2], **setup)]
    return cases


def trace_cases():
    cases = [case([SELL2] * n, quote='spl') for n in (7, 8)]
    cases += [case([SELL2] * n, limit=None, quote='spl') for n in (7, 8)]
    cases += [case([SELL3] * n, limit=None, quote='sol') for n in (21, 22)]
    cases += [case([BUY3] * n, quote='t22', tf=TF) for n in (12, 13)]
    return cases


def budget_cases():
    """The limit sits around the whole joined consumption (lead included);
    `delta` is relative to it, so the non-negative deltas pass."""
    cases = []
    for ops, setup in (([BUY2, SELL2], dict(quote='spl')), ([BUY3, SELL3, EXACT3], dict(quote='t22', tf=TF)),
                       ([SELL3, BUY2], dict(quote='usdc')), ([BUY3, SELL3], dict(quote='sol'))):
        for delta in (150, 149, 0, -1, -1_000):
            cases.append(dict(case(ops, **setup), delta=delta))
    return cases


def default_cases():
    """No limit instruction: the pool is the measured default formula."""
    cases = [
        case([BUY2, SELL2], limit=None, quote='spl'),
        case([SELL2, SELL2, SELL2], limit=None, quote='spl'),
        case([BUY3, SELL3], limit=None, quote='t22', tf=TF),
        # One heavy step (it creates the four quote ATAs) fits a two-step
        # pool but not a one-step pool: the pool is shared, not per-step.
        case([BUY2], limit=None, quote='spl', missing=MISSING4),
        case([BUY2, SELL2], limit=None, quote='spl', missing=MISSING4),
        case([SELL2, BUY2], limit=None, quote='spl', missing=MISSING4),
    ]
    return cases


def random_cases(count=100, seed=20261101):
    rng = random.Random(seed)
    cases = []
    while len(cases) < count:
        quote, tf = rng.choice((('spl', None), ('t22', TF), ('usdc', None)))
        ops, held = [], 10**13
        for _ in range(rng.randrange(1, 7)):
            roll = rng.random()
            if roll < 0.35:
                amount = rng.choice((1, rng.randrange(1, 10**12), rng.randrange(1, 10**13)))
                held += amount // 100
                ops.append((rng.choice(('buy_v2', 'buy_v3')), amount, 10**15, 0))
            elif roll < 0.5:
                ops.append((rng.choice(('exact_v2', 'exact_v3')), rng.randrange(1, 10**10), 1, 0))
                held += 1
            elif roll < 0.85:
                amount = rng.choice((1, rng.randrange(1, 10**12), held + 1))
                ops.append((rng.choice(('sell_v2', 'sell_v3')), amount, 0))
            else:
                ops.append(PAY)
        cases.append(case(ops, limit=rng.choice((None, MAX_LIMIT)), quote=quote, tf=tf))
    return cases


class SameTxTradesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in q.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'same-tx-trades-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        # A chain's first v2 trade creates the creator-vault account
        # with a system transfer: 2,004 units and one trace entry the
        # later steps on the same chain do not pay (the v3 steps list no
        # creator vault and never pay it). The source fixture wipes the
        # vault per case as well, and the separate and joined chains here
        # share the trajectory, so the fold sees the same steps either
        # way; pin the two measurements so a change is loud.
        chain = Chain(quote='spl')
        assert chain.send([SELL2], SEPARATE_LIMIT)['cu'] - LEAD_UNITS == 157_442
        assert chain.send([SELL2], SEPARATE_LIMIT)['cu'] - LEAD_UNITS == 155_438

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, lines):
        out = subprocess.run([str(self.host)], input='\n'.join(lines) + '\n', capture_output=True, text=True,
                             check=True).stdout
        return out.splitlines()

    def wrong(self, item, ran, answer):
        """Why the joined run disagrees with the model's answer, or None."""
        joined = ran['joined']
        fields = answer.split(',')
        payer = str(USER)
        if fields[0] == 'ok':
            fee, saved, units, trace = map(int, fields[1:])
            if joined['err'] is not None:
                return f'expected a pass: {joined["err"]}'
            if (joined['cu'], joined['trace']) != (units, trace):
                return f'units or trace: {joined["cu"], joined["trace"]} != {units, trace}'
            expected = dict(ran['apart'])
            lamports, owner, data = expected[payer]
            expected[payer] = (lamports + saved, owner, data)
            if not any('Log truncated' in line for line in joined['logs']):
                if events(joined['logs']) != ran['emitted']:
                    return 'events differ'
        else:
            index, failure, fee = int(fields[1]), fields[2], int(fields[3])
            if joined['err'] is None:
                return f'expected {failure} at {index}'
            found = int(re.search(r'\((\d+), ', joined['err']).group(1))
            if (found, label(joined['err'])) != (index, failure):
                return f'{found, label(joined["err"])} != {index, failure}'
            expected = dict(ran['before'])
            lamports, owner, data = expected[payer]
            expected[payer] = (lamports - fee, owner, data)
        if ran['after'] != expected:
            return 'end state differs: ' + str([k[:6] for k in expected if expected[k] != ran['after'][k]])
        return None

    def run_cases(self, cases):
        results = [run_case(item) for item in cases]
        answers = self.host_answers([r['line'] for r in results])
        self.assertEqual(len(answers), len(results))
        wrong = [(cases[i]['ops'], w) for i in range(len(cases))
                 for w in [self.wrong(cases[i], results[i], answers[i])] if w]
        self.assertEqual(wrong[:3], [], f'{len(wrong)} of {len(cases)} differ')
        return answers

    def test_merged_fixture_matches_the_source_fixtures(self):
        # The chain's own fixture must reproduce the source packets'
        # outcomes before any joining is believed.
        self.assertIsNone(t3.run_captured(t3.default_case())['error'])
        self.assertIsNone(Chain(quote='sol').send([('sell_v3', 10**12, 0)], SEPARATE_LIMIT)['err'])
        self.assertIsNone(q.run_captured(q.default_case())['error'])
        self.assertIsNone(Chain(quote='spl').send([('sell_v2', 10**12, 0)], SEPARATE_LIMIT)['err'])
        short = q.default_case(op='buy', user_quote=10)
        theirs = q.run_captured(short)['error']
        ours = Chain(quote='spl', user_quote=10).send([BUY2], SEPARATE_LIMIT)
        self.assertEqual(label(ours['err']), f'c{theirs}')

    def test_fixed_cases_match_captured_program(self):
        answers = self.run_cases(fixed_cases())
        kinds = {a.split(',')[2] for a in answers if a.startswith('fail')}
        self.assertTrue({'c6005', 'c6023'} <= kinds, kinds)
        self.assertGreater(sum(a.startswith('ok') for a in answers), 40)

    def test_trace_is_shared(self):
        answers = self.run_cases(trace_cases())
        kinds = {a.split(',')[2] for a in answers if a.startswith('fail')}
        self.assertEqual(kinds, {'trace'}, kinds)

    def test_budget_is_shared(self):
        cases = []
        for item in budget_cases():
            whole = run_case(dict(item, limit=SEPARATE_LIMIT))['joined']['cu']
            cases.append(dict(item, limit=whole + item['delta']))
        answers = self.run_cases(cases)
        self.assertEqual({a.split(',')[2] for a in answers if a.startswith('fail')}, {'budget'})
        self.assertEqual(sum(a.startswith('ok') for a in answers), 12)
        self.assertTrue({2, 3} <= {int(a.split(',')[1]) for a in answers if a.startswith('fail')})

    def test_default_budget_matches_the_formula(self):
        answers = self.run_cases(default_cases())
        by_ops = {tuple(c['ops']): a for c, a in zip(default_cases(), answers)}
        self.assertTrue(by_ops[(BUY2,)].startswith('fail') and by_ops[(BUY2,)].split(',')[2] == 'budget')
        self.assertTrue(by_ops[(BUY2, SELL2)].startswith('fail') and by_ops[(BUY2, SELL2)].split(',')[1] == '1')
        # Transfers widen the pool by 3,000 each at a cost of 150: the
        # flip sits where 200,000 + 3,000k first covers the measured steps.
        probe = Chain(quote='spl', missing=MISSING4)
        heavy = probe.send([BUY2], SEPARATE_LIMIT)['cu'] - LEAD_UNITS
        flip = 0
        while 200_000 + 3_000 * flip < heavy + 150 * flip:
            flip += 1
        cases = [case([PAY] * k + [BUY2], limit=None, quote='spl', missing=MISSING4) for k in (flip - 1, flip)]
        cases.append(case([BUY2] + [PAY] * flip, limit=None, quote='spl', missing=MISSING4))
        answers = self.run_cases(cases)
        self.assertTrue(answers[0].startswith('fail') and answers[0].split(',')[2] == 'budget', answers)
        self.assertTrue(answers[1].startswith('ok'), answers)
        self.assertTrue(answers[2].startswith('ok'), answers)

    def test_budget_and_trace_order_inside_one_step(self):
        # Eight sells fill the trace at the eighth step, whose last trace
        # entry lands `fill` units in. Calibrate `fill` from the joined
        # run itself: the units spent when the trace refusal stops it,
        # less the first seven steps measured apart.
        ops = [SELL2] * 8
        apart = Chain(quote='spl')
        units, emitted = [], []
        for op in ops:
            alone = apart.send([op], SEPARATE_LIMIT)
            units.append(alone['cu'] - LEAD_UNITS)
        joined = Chain(quote='spl').send(ops, MAX_LIMIT)
        self.assertEqual(label(joined['err']), 'trace')
        fill = joined['cu'] - LEAD_UNITS - sum(units[:7])
        self.assertLess(fill, units[7])
        steps = [f'ok:{u}:8:{u}:0' for u in units[:7]] + [f'ok:{units[7]}:8:{fill}:0']

        def answer(limit):
            line = ';'.join([str(limit), *steps])
            return self.host_answers([line])[0]

        whole = LEAD_UNITS + sum(units)
        # A budget that ends one unit short of the whole joined sum runs
        # out in the step's tail, after its trace has filled: trace is
        # reported.
        at_tail = Chain(quote='spl').send(ops, whole - 1)
        self.assertEqual(label(at_tail['err']), 'trace')
        self.assertEqual(answer(whole - 1), 'fail,8,trace,5000')
        # A budget that ends one unit into the step runs out first.
        at_head = Chain(quote='spl').send(ops, LEAD_UNITS + sum(units[:7]) + 1)
        self.assertEqual(label(at_head['err']), 'budget')
        self.assertEqual(answer(LEAD_UNITS + sum(units[:7]) + 1), 'fail,8,budget,5000')

    def test_default_budget_counts_instructions_after_a_failing_prefix(self):
        cases = [case(ops, limit=None, quote='spl', missing=MISSING4, user_quote=0)
                 for ops in ([BUY2, SELL2], [PAY, BUY2, SELL2], [BUY2, SELL2, PAY])]
        answers = self.run_cases(cases)
        self.assertEqual([answer.split(',')[2] for answer in answers], ['c1'] * 3)
        self.assertEqual([int(answer.split(',')[1]) for answer in answers], [0, 1, 0])

    def test_seeded_random_cases_match_captured_program(self):
        answers = self.run_cases(random_cases())
        self.assertGreater(sum(a.startswith('ok') for a in answers), 20)
        self.assertGreater(sum(a.startswith('fail') for a in answers), 10)


if __name__ == '__main__':
    unittest.main()
