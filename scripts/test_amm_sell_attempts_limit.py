"""`attempts.py best N` must not turn a negative count into a slice from the worst row."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'amm_sell/attempts.py'
sys.path.insert(0, str(HERE / 'amm_sell'))
from sell_score import SCORE_VERSION


def attempt(lane, distance):
    return {'schema': 'amm-sell-attempt-v1', 'lane': lane, 'approach': 'probe',
            'status': 'scored', 'hypothesis': 'synthetic ledger query control',
            'metrics': {'score_version': SCORE_VERSION, 'lost_windows_count': 0,
                        'lost_windows_normalized_count': 0, 'sell_raw_equal': False,
                        'sell_size': 9024, 'align_distance': distance, 'slot_diffs': 20}}


ROWS = [attempt('best', 1), attempt('middle', 2), attempt('worst', 3)]


class AttemptBestLimitTests(unittest.TestCase):
    def best(self, *extra):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / 'ATTEMPTS.jsonl'
            ledger.write_text(''.join(json.dumps(row) + '\n' for row in ROWS), encoding='utf-8')
            return subprocess.run([sys.executable, '-B', str(SCRIPT), 'best', *extra],
                                  env={**os.environ, 'AMM_SELL_SWARM': directory},
                                  capture_output=True, text=True)

    def test_negative_count_is_rejected(self):
        for value in ['-1', '-3']:
            result = self.best(value)
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertEqual(result.stdout, '')
            self.assertIn('must not be negative', result.stderr)

    def test_zero_and_positive_counts_stay_admitted(self):
        self.assertEqual(self.best('0').stdout, '')
        result = self.best('2')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([line.split('/')[0] for line in result.stdout.splitlines()],
                         ['best', 'middle'])


if __name__ == '__main__':
    unittest.main()
