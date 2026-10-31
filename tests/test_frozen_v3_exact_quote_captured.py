"""Captured-program checks for exact-quote buys that touch a frozen token account.

Every fixed and random case of `tests/test_v3_exact_quote_captured.py`
(`buy_exact_quote_in_v3` and the crossing `buy_v3`) runs on the captured
`evidence/original/pump/deployed.so` once as written and once per token
account it holds with that account frozen (state byte 2): the user's and
the curve's base accounts, and on token-quote routes also the user's and
the curve's quote accounts and the buyback recipient's. The unfrozen twin's
ending goes to `programs/pump/recovered/frozen_v3_exact_quote_host.rs`,
whose answer must equal it. The host model judges each leg by its gross
transfer amount — the amount its transfer helper is invoked with, before
any transfer fee is withheld — taken from the accounting model's answer:
the base leg's is `base_moved` plus the post-complete fill, the quote
leg's is the curve's net quote plus the quote transfer fee, and the
buyback leg's is what remains of the user's gross quote outlay. A frozen
run that fails must also leave every watched account byte-identical
(only the 5,000-lamport transaction fee is paid), and a frozen run that
still succeeds must land exactly as its twin, apart from the frozen
account's own state byte. This shows matching behavior on these inputs
only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import importlib
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
HOST_SOURCE = ROOT / 'programs/pump/recovered/frozen_v3_exact_quote_host.rs'
FROZEN_STATE_OFFSET = 108
FROZEN_STATE = 2
TX_FEE = 5_000

base = importlib.import_module('test_v3_exact_quote_captured')
USER = base.USER.pubkey()
TOKEN_IDS = {str(base.TOKEN), str(base.TOKEN22)}


class Recorder:
    """The base module's LiteSVM, keeping the last transaction's logs."""

    logs = []
    transfers = []

    def __init__(self, real):
        self.vm = real()

    def __getattr__(self, name):
        attr = getattr(self.vm, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            answer = attr(*args, **kwargs)
            if type(answer) is type(self.vm):
                self.vm = answer
                return self
            return answer
        return call

    def send_transaction(self, tx):
        result = self.vm.send_transaction(tx)
        meta = result.meta() if hasattr(result, 'meta') else result
        Recorder.logs = list(meta.logs())
        keys = list(tx.message.account_keys)
        Recorder.transfers = []
        for group in meta.inner_instructions():
            for inner in group:
                ix = inner.instruction()
                data = bytes(ix.data)
                if str(ix.program_id(keys)) not in TOKEN_IDS or not data:
                    continue
                # Transfer and TransferChecked identify source/destination.
                if data[0] not in (3, 12):
                    continue
                indices = list(ix.accounts)
                destination = 2 if data[0] == 12 else 1
                Recorder.transfers.append((keys[indices[0]], keys[indices[destination]]))
        return result


def freezing(mint, owner):
    original = base.token_bytes

    def token_bytes(mint_key, o, amount, with_fee_ext=False):
        data = bytearray(original(mint_key, o, amount, with_fee_ext))
        if bytes(mint_key) == bytes(mint) and bytes(o) == bytes(owner):
            data[FROZEN_STATE_OFFSET] = FROZEN_STATE
        return bytes(data)
    return mock.patch.object(base, 'token_bytes', token_bytes)


def ending(captured):
    error = captured['error']
    if error is None:
        return 'done'
    if isinstance(error, int):
        return str(error)
    code = re.search(r'Custom\((\d+)\)', str(error))
    return code.group(1) if code else str(error)


def invoked_legs(c, transfers):
    """Identify physical transfer legs from the unfrozen twin's actual CPIs."""
    r = base.roles(c)
    mask = 0
    for source, destination in transfers:
        if source == r['curve_base'] and destination == r['user_base']:
            mask |= 1
        elif not r['native'] and source == r['user_quote'] and destination == r['curve_quote']:
            mask |= 2
        elif not r['native'] and source == r['user_quote'] and destination == r['recipient']:
            mask |= 4
        else:
            raise AssertionError(('unrecognized transfer leg', source, destination))
    return mask


def slots(c):
    """(host name, mint, owner, snapshot key name) per token account of the case."""
    r = base.roles(c)
    out = [('user_base', base.BASE, USER, 'user_base'), ('curve_base', base.BASE, base.CURVE, 'curve_base')]
    if not r['native']:
        out += [('user_quote', r['quote_mint'], USER, 'user_quote'),
                ('curve_quote', r['quote_mint'], base.CURVE, 'curve_quote'),
                ('recipient', r['quote_mint'], base.BUYBACK, 'recipient')]
    return out


def gross_amounts(answer):
    """Each leg's gross transfer amount from the accounting model's answer.

    The base leg moves the curve fill plus the post-complete fill; the
    quote leg moves the pool quote before the transfer fee, which is the
    curve's net quote plus that fee; the buyback leg moves what is left
    of the user's gross outlay once the quote leg is taken out.
    """
    m = answer[1]
    quote_gross = m['curve_quote'] + m['quote_transfer_fee']
    return (m['base_moved'] + m.get('post_base_out', 0), quote_gross, -m['user_quote'] - quote_gross)


class FrozenV3ExactQuoteCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in base.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'frozen-v3-exact-quote-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answer(self, line):
        return subprocess.run([str(self.host)], input=line + '\n', capture_output=True, text=True, check=True).stdout.strip()

    def check_state(self, label, account, twin, frozen_run, frozen_key):
        """The frozen run's footprint: nothing on failure, the twin's on success."""
        if frozen_run['error'] is not None:
            for key, before in frozen_run['before'].items():
                after = frozen_run['after'][key]
                self.assertEqual(after is None, before is None, (label, account, key))
                if before is None:
                    continue
                self.assertEqual(after[1], before[1], (label, account, key, 'data'))
                self.assertEqual(after[2], before[2], (label, account, key, 'owner'))
                want = -TX_FEE if key == USER else 0
                self.assertEqual(after[0] - before[0], want, (label, account, key, 'lamports'))
            return
        for key, want in twin['after'].items():
            got = frozen_run['after'][key]
            self.assertEqual(got is None, want is None, (label, account, key))
            if want is None:
                continue
            self.assertEqual(got[0], want[0], (label, account, key, 'lamports'))
            self.assertEqual(got[2], want[2], (label, account, key, 'owner'))
            got_data, want_data = got[1], want[1]
            if key == frozen_key and len(got_data) > FROZEN_STATE_OFFSET:
                got_data = bytearray(got_data)
                want_data = bytearray(want_data)
                got_data[FROZEN_STATE_OFFSET] = want_data[FROZEN_STATE_OFFSET] = 0
            self.assertEqual(bytes(got_data), bytes(want_data), (label, account, key, 'data'))
        self.assertEqual(frozen_run['events'], twin['events'], (label, account, 'events'))
        self.assertEqual(frozen_run['cpi'], twin['cpi'], (label, account, 'cpi'))

    def run_cases(self, cases):
        answers = base.model([c for _, c in cases])
        real = base.LiteSVM
        seen = set()
        runs = 0
        with mock.patch.object(base, 'LiteSVM', lambda: Recorder(real)):
            for (label, c), answer in zip(cases, answers):
                if answer[0] == 'unmodelled':
                    continue
                r = base.roles(c)
                twin = base.run_captured(c)
                twin_end = ending(twin)
                self.assertTrue(twin_end == 'done' or twin_end.isdigit(), (label, twin_end))
                legs = invoked_legs(c, Recorder.transfers)
                gross = gross_amounts(answer) if answer[0] == 'ok' else (0, 0, 0)
                self.assertGreaterEqual(gross[2], 0, (label, gross))
                for name, mint, owner, key_name in slots(c):
                    line = (f"{name},{twin_end},{legs},{gross[0]},{gross[1]},{gross[2]},"
                            f"{int(r['program'] == base.TOKEN22)}")
                    expected = self.answer(line)
                    with self.subTest(label=label, account=name, twin=twin_end):
                        with freezing(mint, owner):
                            frozen_run = base.run_captured(c)
                        self.assertEqual(ending(frozen_run), expected)
                        self.check_state(label, name, twin, frozen_run, r[key_name])
                    seen.add((name, twin_end, expected))
                    runs += 1
        return seen, runs

    def test_fixed_cases(self):
        seen, runs = self.run_cases(base.fixed_cases())
        self.assertGreater(runs, 3_000)
        # every family the model names actually occurs in the fixed cases
        self.assertIn(('user_base', 'done', '17'), seen)        # plain crossing: post-complete fill runs the base leg
        self.assertIn(('curve_base', 'done', 'done'), seen)     # Mayhem crossing: no fill, the base leg never runs
        self.assertIn(('recipient', 'done', '17'), seen)        # buyback fully withheld by its transfer fee
        self.assertIn(('recipient', 'done', 'done'), seen)      # empty buyback leg
        self.assertIn(('user_base', '6024', '17'), seen)        # accrual overflow after the base leg
        self.assertIn(('recipient', '6024', '6024'), seen)      # buyback leg not reached by 6024
        self.assertIn(('curve_base', '1', '17'), seen)          # base leg is the failing transfer
        self.assertIn(('recipient', '1', '1'), seen)            # Token-2022 destination of the failing leg
        self.assertTrue(any(e == '17' and t == 'done' for _, t, e in seen))

    def test_zero_base_leg_before_insufficient_quote(self):
        cases = [(label + '-insufficient-quote', dict(c, user_quote=0))
                 for label, c in base.fixed_cases()
                 if label in ('wsol-cross-rtr-zero-mayhem', 'usdc-cross-rtr-zero-mayhem')]
        self.assertEqual(len(cases), 2)
        seen, runs = self.run_cases(cases)
        self.assertEqual(runs, 10)
        self.assertIn(('user_base', '1', '1'), seen)
        self.assertIn(('user_quote', '1', '17'), seen)
        self.assertIn(('curve_quote', '1', '17'), seen)

    def test_random_cases(self):
        seen, runs = self.run_cases(base.random_cases())
        self.assertGreater(runs, 500)
        self.assertTrue(any(e == '17' and t == 'done' for _, t, e in seen))

    def test_model_answers(self):
        # plain crossing, zero curve fill: the post-complete fill still runs the base leg
        self.assertEqual(self.answer('user_base,done,1,164948452885110,995308642,4691358,0'), '17')
        # Mayhem crossing: delivered is zero, the base leg never runs; the quote leg still does
        self.assertEqual(self.answer('user_base,done,0,0,3,0,0'), 'done')
        self.assertEqual(self.answer('curve_base,done,1,0,3,0,1'), 'done')
        self.assertEqual(self.answer('user_quote,done,1,0,3,0,1'), '17')
        self.assertEqual(self.answer('recipient,done,1,0,3,0,1'), 'done')
        # a buyback the transfer fee withholds in full: net zero, gross positive
        self.assertEqual(self.answer('recipient,done,3,3292089162,995310000,469,1'), '17')
        # the fee-accrual overflow is raised after the base leg only
        self.assertEqual(self.answer('user_base,6024,1,0,0,0,0'), '17')
        self.assertEqual(self.answer('recipient,6024,1,0,0,0,0'), '6024')
        self.assertEqual(self.answer('user_base,6024,0,0,0,0,0'), '6024')
        self.assertEqual(self.answer('user_base,6003,0,0,0,0,0'), '6003')
        # InsufficientFunds: earlier legs turn frozen, later legs are never reached
        self.assertEqual(self.answer('curve_base,1,1,0,0,0,0'), '17')
        self.assertEqual(self.answer('user_quote,1,1,0,0,0,0'), '1')
        self.assertEqual(self.answer('curve_quote,1,7,0,0,0,0'), '17')
        self.assertEqual(self.answer('recipient,1,7,0,0,0,0'), '17')
        self.assertEqual(self.answer('recipient,1,7,0,0,0,1'), '1')
        self.assertEqual(self.answer('user_quote,1,2,0,0,0,1'), '17')
        self.assertEqual(self.answer('curve_quote,1,2,0,0,0,1'), '1')


if __name__ == '__main__':
    unittest.main()
