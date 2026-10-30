"""Recording after a valid unterminated JSON row must not corrupt the ledger."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class LedgerSeparatorTests(unittest.TestCase):
    def record(self, initial):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'attempts.jsonl'
            ledger.write_bytes(initial)
            result = subprocess.run([sys.executable, '-B',
                str(Path(__file__).with_name('log_attempt.py')), 'record',
                '--lane', 'test', '--approach', 'synthetic', '--target', '0x10',
                '--dedupe-key', 'new-attempt', '--hypothesis', 'test only', '--status', 'analyzed'],
                env={**os.environ, 'PUMP_SWARM_LEDGER': str(ledger)},
                capture_output=True, text=True)
            return result, ledger.read_bytes()

    def test_unterminated_row_remains_parseable(self):
        initial = b'{"dedupe_key":"old-attempt"}'
        result, raw = self.record(initial)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in raw.splitlines()]
        self.assertEqual([r['dedupe_key'] for r in rows], ['old-attempt', 'new-attempt'])
        self.assertTrue(raw.startswith(initial + b'\n'))

    def test_terminated_row_gets_no_blank_line(self):
        result, raw = self.record(b'{"dedupe_key":"old-attempt"}\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(raw.splitlines()), 2)
        self.assertNotIn(b'\n\n', raw)

    def test_empty_ledger_gets_one_record(self):
        result, raw = self.record(b'')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(raw.splitlines()), 1)

    def test_corrupt_last_row_is_not_repaired_or_appended(self):
        initial = b'{"dedupe_key":'
        result, raw = self.record(initial)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(raw, initial)


if __name__ == '__main__':
    unittest.main()
