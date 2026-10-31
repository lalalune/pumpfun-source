"""`attempts.py seen` must answer for the sell.rs an attempt compiled."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ATTEMPTS = ROOT / 'scripts/amm_sell/attempts.py'
BASELINE = b'// baseline sell\n'
PATCHED = b'// baseline sell after a patch\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def attempt(approach, input_sell, compiled=None, patch=None):
    entry = {'schema': 'amm-sell-attempt-v1', 'lane': 'l', 'approach': approach, 'hypothesis': 'h',
             'status': 'scored', 'inputs': {'sell': input_sell, 'patch': patch, 'flags': ''}}
    if compiled is not None:
        entry['output_sha256'] = {'sell.rs': compiled}
    return entry


class AttemptsSeenTests(unittest.TestCase):
    def seen(self, entries, data):
        with tempfile.TemporaryDirectory(prefix='amm-attempts-seen-') as temporary:
            swarm = Path(temporary)
            lines = ''.join(json.dumps(entry) + '\n' for entry in entries)
            (swarm / 'ATTEMPTS.jsonl').write_text(lines, encoding='utf-8')
            source = swarm / 'query.rs'
            source.write_bytes(data)
            environment = dict(os.environ, AMM_SELL_SWARM=str(swarm))
            result = subprocess.run([sys.executable, '-B', str(ATTEMPTS), 'seen', str(source)],
                                    env=environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        return [] if result.stdout.strip() == 'unseen' else json.loads(result.stdout)

    def test_patched_build_is_found_by_its_compiled_source(self):
        entry = attempt('patched', sha(BASELINE), sha(PATCHED), patch='p' * 64)
        self.assertEqual([row['approach'] for row in self.seen([entry], PATCHED)], ['patched'])

    def test_patched_build_did_not_compile_the_baseline_file(self):
        entry = attempt('patched', sha(BASELINE), sha(PATCHED), patch='p' * 64)
        self.assertEqual(self.seen([entry], BASELINE), [])

    def test_direct_and_older_entries_keep_their_input_hash(self):
        direct = attempt('direct', sha(BASELINE), sha(BASELINE))
        older = attempt('older', sha(BASELINE))
        self.assertEqual([row['approach'] for row in self.seen([direct, older], BASELINE)],
                         ['direct', 'older'])


if __name__ == '__main__':
    unittest.main()
