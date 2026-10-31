"""Captured-program checks for v3 trades that touch a frozen token account.

Every fixed case of `tests/test_v3_trade_accounting_captured.py` runs on the
captured `evidence/original/pump/deployed.so` once as written and once per
token account it holds with that account frozen (state byte 2): the user's
and the curve's base accounts, and on token-quote routes also the user's and
the curve's quote accounts and the buyback recipient's. The frozen run's
ending goes to `programs/pump/recovered/frozen_v3_trade_host.rs`, whose
answer must equal it. A frozen run that fails must also leave every watched
account byte-identical (only the 5,000-lamport transaction fee is paid), and
a frozen run that still succeeds must land exactly as its twin, apart from
the frozen account's own state byte. This shows matching behavior on these
inputs only; it is not a byte-identity claim.
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
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/frozen_v3_trade_host.rs'
FROZEN_STATE_OFFSET = 108
FROZEN_STATE = 2
TX_FEE = 5_000

base = importlib.import_module('test_v3_trade_accounting_captured')
USER = base.USER.pubkey()
TOKEN_IDS = {str(base.TOKEN), str(base.TOKEN22)}


class Recorder:
    """The base module's LiteSVM, keeping the last transaction's logs."""

    logs = []

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


def token_invokes(logs):
    return sum(1 for line in logs if line.startswith('Program ') and line.split()[1] in TOKEN_IDS
               and line.split()[2] == 'invoke')


def slots(c):
    """(host name, mint, owner, snapshot key name) per token account of the case."""
    r = base.roles(c)
    out = [('user_base', base.BASE, USER, 'user_base'), ('curve_base', base.BASE, base.CURVE, 'curve_base')]
    if not r['native']:
        out += [('user_quote', r['quote_mint'], USER, 'user_quote'),
                ('curve_quote', r['quote_mint'], base.CURVE, 'curve_quote'),
                ('recipient', r['quote_mint'], base.BUYBACK, 'recipient')]
    return out


class FrozenV3TradeCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'frozen-v3-trade-host'
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

    def test_fixed_cases(self):
        cases = base.fixed_cases()
        answers = base.model([c for _, c in cases])
        real = base.LiteSVM
        seen = set()
        with mock.patch.object(base, 'LiteSVM', lambda: Recorder(real)):
            for (label, c), answer in zip(cases, answers):
                r = base.roles(c)
                twin = base.run_captured(c)
                twin_end = ending(twin)
                self.assertTrue(twin_end == 'done' or twin_end.isdigit(), (label, twin_end))
                invokes = token_invokes(Recorder.logs)
                if answer[0] == 'ok':
                    m = answer[1]
                    quote_moves = int(m['user_quote' if c['buy'] else 'curve_quote'] != 0)
                    buyback_moves = int(m['buyback_recipient'] != 0)
                else:
                    quote_moves = buyback_moves = 0
                side = 'buy' if c['buy'] else 'sell'
                for name, mint, owner, key_name in slots(c):
                    line = (f"{side},{name},{twin_end},{invokes},{quote_moves},{buyback_moves},"
                            f"{int(r['program'] == base.TOKEN22)}")
                    expected = self.answer(line)
                    with self.subTest(label=label, account=name, twin=twin_end):
                        with freezing(mint, owner):
                            frozen_run = base.run_captured(c)
                        self.assertEqual(ending(frozen_run), expected)
                        self.check_state(label, name, twin, frozen_run, r[key_name])
                    seen.add((side, name, twin_end, expected))
        # every family the model names actually occurs in the fixed cases
        self.assertIn(('sell', 'recipient', 'done', 'done'), seen)       # empty buyback leg
        self.assertIn(('sell', 'user_quote', 'done', 'done'), seen)      # empty quote leg
        self.assertIn(('sell', 'user_base', '6024', '17'), seen)         # accrual after transfers
        self.assertIn(('sell', 'recipient', '6024', '6024'), seen)       # buyback leg not reached
        self.assertIn(('buy', 'curve_quote', '1', '1'), seen)            # Token-2022 destination
        self.assertIn(('buy', 'recipient', '1', '17'), seen)             # SPL Token failing leg
        self.assertTrue(any(e == '17' and t == 'done' for _, _, t, e in seen))

    def test_model_answers(self):
        self.assertEqual(self.answer('buy,user_base,done,3,1,1,0'), '17')
        self.assertEqual(self.answer('sell,recipient,done,3,1,0,0'), 'done')
        self.assertEqual(self.answer('sell,user_quote,done,3,0,1,0'), 'done')
        self.assertEqual(self.answer('sell,curve_base,6024,2,0,0,0'), '17')
        self.assertEqual(self.answer('sell,recipient,6024,2,0,0,0'), '6024')
        self.assertEqual(self.answer('sell,user_base,6024,0,0,0,0'), '6024')
        self.assertEqual(self.answer('sell,user_base,6003,0,0,0,0'), '6003')
        self.assertEqual(self.answer('buy,curve_base,1,2,0,0,0'), '17')
        self.assertEqual(self.answer('buy,curve_quote,1,1,0,0,0'), '1')
        self.assertEqual(self.answer('buy,user_quote,1,2,0,0,1'), '17')
        self.assertEqual(self.answer('buy,curve_quote,1,2,0,0,1'), '1')
        self.assertEqual(self.answer('buy,recipient,1,2,0,0,0'), '1')
        self.assertEqual(self.answer('buy,recipient,1,3,0,0,0'), '17')
        self.assertEqual(self.answer('buy,recipient,1,3,0,0,1'), '1')


if __name__ == '__main__':
    unittest.main()
