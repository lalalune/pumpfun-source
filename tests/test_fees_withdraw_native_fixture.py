"""The existing WSOL withdrawal case must execute a native token transfer."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WithdrawNativeFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='withdraw-native-')
        cls.addClassCleanup(temporary.cleanup)
        output = Path(temporary.name) / 'report.json'
        result = subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts/fees_withdraw_differential.py'),
             '--candidate', str(ROOT / 'evidence/original/pump_fees/deployed.so'),
             '--output', str(output)],
            capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.report = json.loads(output.read_text(encoding='utf-8'))
        cls.rows = {row['case']['name']: row for row in cls.report['cases']}

    @staticmethod
    def token(account):
        raw = bytes.fromhex(account['data'])
        return {
            'amount': int.from_bytes(raw[64:72], 'little'),
            'native_tag': int.from_bytes(raw[109:113], 'little'),
            'reserve': int.from_bytes(raw[113:121], 'little'),
        }

    def test_existing_wsol_case_has_native_accounts_and_mint(self):
        for side in ('original', 'candidate'):
            row = self.rows['wsol'][side]
            with self.subTest(side=side):
                self.assertIsNone(row['error'])
                self.assertEqual(bytes.fromhex(row['before']['quote_mint']['data'])[44], 9)
                for name in ('actual_source', 'actual_dest'):
                    account = row['before'][name]
                    state = self.token(account)
                    self.assertEqual(state['native_tag'], 1)
                    self.assertGreater(state['reserve'], 0)
                    self.assertEqual(account['lamports'], state['reserve'] + state['amount'])

    def test_wsol_transfer_moves_backing_lamports(self):
        for side in ('original', 'candidate'):
            row = self.rows['wsol'][side]
            before, after = row['before'], row['after']
            amount = self.token(before['actual_source'])['amount']
            with self.subTest(side=side):
                self.assertGreater(amount, 0)
                self.assertEqual(before['actual_source']['lamports'] - after['actual_source']['lamports'], amount)
                self.assertEqual(after['actual_dest']['lamports'] - before['actual_dest']['lamports'], amount)
                self.assertEqual(self.token(after['actual_source'])['amount'], 0)
                self.assertEqual(self.token(after['actual_dest'])['amount'],
                                 self.token(before['actual_dest'])['amount'] + amount)

    def test_ordinary_token_cases_keep_non_native_balances(self):
        self.assertEqual(self.report['mismatches'], [])
        self.assertTrue(all(row['match'] for row in self.report['cases']))
        for name in ('token', 'token22'):
            row = self.rows[name]['original']
            with self.subTest(case=name):
                self.assertIsNone(row['error'])
                self.assertEqual(bytes.fromhex(row['before']['quote_mint']['data'])[44], 6)
                for account in ('actual_source', 'actual_dest'):
                    self.assertEqual(self.token(row['before'][account])['native_tag'], 0)
                    self.assertEqual(row['before'][account]['lamports'], row['after'][account]['lamports'])


if __name__ == '__main__':
    unittest.main()
