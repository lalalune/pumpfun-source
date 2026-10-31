"""Captured-program checks for trades that touch a frozen token account.

Every fixed case of the legacy and v2 native trade tests runs on the captured
`evidence/original/pump/deployed.so` three times: as written, with the curve's
token account frozen, and with the user's frozen. The twin run's ending goes to
`programs/pump/recovered/frozen_trade_host.rs`, whose answer must equal both
frozen runs. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/frozen_trade_host.rs'
MODULES = {'test_legacy_buy_captured': 'buy', 'test_legacy_sell_captured': 'sell',
           'test_buy_v2_captured': 'buy', 'test_sell_v2_captured': 'sell_v2'}
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
FROZEN_STATE_OFFSET = 108
FROZEN_STATE = 2


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


def freezing(base, frozen_owner):
    original = base.token_data

    def token_data(owner, *args, **kwargs):
        data = bytearray(original(owner, *args, **kwargs))
        if owner == frozen_owner:
            data[FROZEN_STATE_OFFSET] = FROZEN_STATE
        return bytes(data)
    return mock.patch.object(base, 'token_data', token_data)


def ending(captured):
    error = captured.get('error')
    if error is None:
        return 'done'
    if isinstance(error, int):
        return str(error)
    code = re.search(r'Custom\((\d+)\)', str(error))
    if code:
        return code.group(1)
    if 'ProgramFailed' in str(error) or any('panicked' in line for line in Recorder.logs):
        ran = any(line.startswith(f'Program {TOKEN} invoke') for line in Recorder.logs)
        return f'panic:{int(ran)}'
    return str(error)


class FrozenTradeCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'frozen-trade-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answer(self, line):
        return subprocess.run([str(self.host)], input=line + '\n', capture_output=True, text=True, check=True).stdout.strip()

    def run_module(self, name):
        base = importlib.import_module(name)
        side = MODULES[name]
        real = base.LiteSVM
        endings = set()
        with mock.patch.object(base, 'LiteSVM', lambda: Recorder(real)):
            for item in base.fixed_cases():
                twin = ending(base.run_captured(item))
                endings.add(twin)
                expected = self.answer(f'{side},{twin}').replace('panic', twin)
                for owner in (base.CURVE, base.USER.pubkey()):
                    with self.subTest(module=name, twin=twin, owner=str(owner)), freezing(base, owner):
                        self.assertEqual(ending(base.run_captured(item)), expected)
        return endings

    def test_legacy_buy(self):
        self.assertIn('done', self.run_module('test_legacy_buy_captured'))

    def test_legacy_sell(self):
        self.assertTrue({'done', '6062', '6074'} <= self.run_module('test_legacy_sell_captured'))

    def test_buy_v2(self):
        self.assertIn('done', self.run_module('test_buy_v2_captured'))

    def test_sell_v2(self):
        self.assertIn('done', self.run_module('test_sell_v2_captured'))

    def test_model_answers_every_side(self):
        self.assertEqual(self.answer('buy,done'), '17')
        self.assertEqual(self.answer('buy,6057'), '6057')
        self.assertEqual(self.answer('sell,6057'), '17')
        self.assertEqual(self.answer('sell,6003'), '6003')
        self.assertEqual(self.answer('sell_v2,6057'), '6057')
        self.assertEqual(self.answer('sell_v2,6062'), '17')
        self.assertEqual(self.answer('sell,panic:1'), '17')
        self.assertEqual(self.answer('sell,panic:0'), 'panic')


if __name__ == '__main__':
    unittest.main()
