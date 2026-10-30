"""`search --limit` must print exactly as many rows as its header reports."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('log_attempt.py')
ROWS = [
    {'schema': 'main-pump-attempt-v1', 'attempt_id': f'id-{n}', 'lane': 'test', 'target': '0x10',
     'status': 'analyzed', 'dedupe_key': f'attempt-{n}', 'hypothesis': 'test only', 'data': {}}
    for n in range(3)
]


class LedgerLimitTests(unittest.TestCase):
    def search(self, *extra):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'attempts.jsonl'
            ledger.write_text(''.join(json.dumps(r) + '\n' for r in ROWS))
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), 'search', '--target', '0x10', *extra],
                env={**os.environ, 'PUMP_SWARM_LEDGER': str(ledger)}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            return [json.loads(line) for line in lines if not line.startswith('# ')], lines[-1]

    def test_limit_zero_prints_nothing(self):
        rows, header = self.search('--limit', '0')
        self.assertEqual(rows, [])
        self.assertEqual(header, '# 3 matching rows (0 shown, newest last)')

    def test_limit_one_prints_newest(self):
        rows, header = self.search('--limit', '1')
        self.assertEqual([r['dedupe_key'] for r in rows], ['attempt-2'])
        self.assertEqual(header, '# 3 matching rows (1 shown, newest last)')

    def test_limit_above_count_prints_all(self):
        rows, header = self.search('--limit', '9')
        self.assertEqual(len(rows), 3)
        self.assertEqual(header, '# 3 matching rows (3 shown, newest last)')

    def test_default_limit_prints_all_below_cap(self):
        rows, header = self.search()
        self.assertEqual(len(rows), 3)
        self.assertEqual(header, '# 3 matching rows (3 shown, newest last)')


if __name__ == '__main__':
    unittest.main()
