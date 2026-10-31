#!/usr/bin/env python3
"""A failed BEST write keeps the previous record for the next AMM attempt."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
LIMIT = 8000
# A real short write: the ledger line stays under the file size limit, while
# the indented BEST document crosses it.
CHILD = '''
import json, resource, signal, sys
signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
sys.path.insert(0, sys.argv[1])
import try_sell
if int(sys.argv[2]):
    resource.setrlimit(resource.RLIMIT_FSIZE, (int(sys.argv[2]), int(sys.argv[2])))
entry = {'status': 'scored', 'hypothesis': 'large', 'padding': [0] * 2000,
         'metrics': {'score_version': try_sell.sell_score.SCORE_VERSION,
                     'lost_windows_normalized_count': 0, 'sell_raw_equal': False,
                     'sell_size': 9024, 'align_distance': 1, 'slot_diffs': 1}}
try:
    try_sell.locked_append(entry)
except OSError:
    sys.exit(7)
'''


def append(root, limit):
    env = dict(os.environ, AMM_SELL_SWARM=str(root))
    return subprocess.run([sys.executable, '-B', '-c', CHILD, str(HERE / 'amm_sell'), str(limit)],
                          env=env, capture_output=True, text=True, timeout=60)


def best_path(root):
    code = 'import sys;sys.path.insert(0,sys.argv[1]);import sell_score;print(sell_score.SCORE_VERSION)'
    version = subprocess.check_output([sys.executable, '-B', '-c', code, str(HERE / 'amm_sell')], text=True).strip()
    return root / f'BEST-v{version}.json'


class BestPublicationTests(unittest.TestCase):
    def test_failed_replacement_keeps_the_prior_best(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            best = best_path(root)
            prior = json.dumps({'rank': [10**9] * 4, 'entry': {'attempt_id': 'prior'}}).encode()
            best.write_bytes(prior)

            failed = append(root, LIMIT)
            self.assertEqual(failed.returncode, 7, failed.stderr)
            self.assertEqual(best.read_bytes(), prior)
            self.assertEqual([path.name for path in root.iterdir() if path.name.startswith('.BEST')], [])

            retried = append(root, 0)
            self.assertEqual(retried.returncode, 0, retried.stderr)
            self.assertEqual(json.loads(best.read_bytes())['entry']['hypothesis'], 'large')


if __name__ == '__main__':
    unittest.main()
