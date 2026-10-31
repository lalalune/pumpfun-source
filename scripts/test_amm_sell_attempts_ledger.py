#!/usr/bin/env python3
"""One torn ledger line must not hide the other AMM attempts from attempts.py."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parent / 'amm_sell/attempts.py'


def attempts(root, *arguments):
    return subprocess.run([sys.executable, '-B', str(TOOL), *arguments], capture_output=True, text=True,
                          env=dict(os.environ, AMM_SELL_SWARM=str(root)), timeout=60)


class AttemptsLedgerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.row = json.dumps({'schema': 'amm-sell-attempt-v1', 'lane': 'lane-a', 'approach': 'tag',
                               'hypothesis': 'kept', 'status': 'build_failed',
                               'inputs': {'sell': 'a' * 64, 'patch': None, 'flags': ''}})

    def ledger(self, *lines):
        (self.root / 'ATTEMPTS.jsonl').write_text(''.join(line + '\n' for line in lines))

    def test_torn_line_keeps_the_other_attempts_readable(self):
        self.ledger(self.row, self.row[:40])
        result = attempts(self.root, 'summary')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('1 builds, 0 notes', result.stdout)
        self.assertIn('ATTEMPTS.jsonl:2: skipping malformed entry', result.stderr)

    def test_json_row_that_is_not_an_entry_is_skipped(self):
        self.ledger('5', self.row)
        result = attempts(self.root, 'grep', 'kept')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('lane-a/tag', result.stdout)
        self.assertIn('ATTEMPTS.jsonl:1: skipping malformed entry', result.stderr)

    def test_note_is_still_recorded_after_a_torn_line(self):
        self.ledger(self.row[:40])
        result = attempts(self.root, 'note', '--lane', 'lane-a', '--approach', 'tag',
                          '--kind', 'finding', '--text', 'after the torn line')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('after the torn line', (self.root / 'ATTEMPTS.jsonl').read_text())


if __name__ == '__main__':
    unittest.main()
