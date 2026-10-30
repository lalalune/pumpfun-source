"""`search --limit` must not turn a negative count into a slice from the oldest row."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('log_attempt.py')
ROWS = [
    {'schema': 'main-pump-attempt-v1', 'attempt_id': f'id-{n}', 'timestamp_utc': f'2026-10-29T00:00:0{n}+00:00',
     'lane': 'test', 'approach': 'synthetic', 'target': '0x10',
     'status': 'analyzed', 'dedupe_key': f'attempt-{n}', 'hypothesis': 'test only', 'data': {}}
    for n in range(3)
]


class LedgerNegativeLimitTests(unittest.TestCase):
    def search(self, *extra):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'attempts.jsonl'
            ledger.write_text(''.join(json.dumps(r) + '\n' for r in ROWS))
            return subprocess.run([sys.executable, '-B', str(SCRIPT), 'search', *extra],
                                  env={**os.environ, 'PUMP_SWARM_LEDGER': str(ledger)},
                                  capture_output=True, text=True)

    def test_negative_limit_is_rejected(self):
        for value in ['-1', '-3']:
            result = self.search('--limit', value)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertEqual(result.stdout, '')
            self.assertIn('--limit', result.stderr)

    def test_zero_and_positive_limits_stay_admitted(self):
        self.assertEqual(self.search('--limit', '0').returncode, 0)
        self.assertEqual(self.search('--limit', '2').returncode, 0)


if __name__ == '__main__':
    unittest.main()
