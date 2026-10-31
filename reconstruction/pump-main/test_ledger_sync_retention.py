"""sync must not drop committed attempts the live ledger has never seen."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import log_attempt


def row(name):
    return {'schema': 'main-pump-attempt-v1', 'attempt_id': name + '-id', 'timestamp_utc': '2026-10-29T00:00:00+00:00',
            'lane': 'test', 'approach': 'synthetic', 'target': '0x10', 'dedupe_key': name,
            'hypothesis': 'test only', 'status': 'analyzed', 'data': {}}


def text(*rows):
    return ''.join(json.dumps(item) + '\n' for item in rows)


class LedgerSyncRetentionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.ledger = self.root / 'live/ATTEMPTS.jsonl'
        self.ledger.parent.mkdir()
        self.tracked = self.root / 'tracked.jsonl'
        patcher = patch.multiple(log_attempt, LEDGER=self.ledger,
                                 LOCK=self.ledger.with_name('.attempts.lock'), TRACKED=self.tracked)
        patcher.start()
        self.addCleanup(patcher.stop)

    def sync(self):
        with patch.object(sys, 'argv', ['log_attempt.py', 'sync']), contextlib.redirect_stdout(io.StringIO()):
            log_attempt.main()

    def test_sync_refuses_to_drop_rows_only_in_the_snapshot(self):
        self.ledger.write_text(text(row('shared'), row('local')), encoding='utf-8')
        snapshot = text(row('shared'), row('merged-from-another-host'))
        self.tracked.write_text(snapshot, encoding='utf-8')
        with self.assertRaisesRegex(SystemExit, 'merged-from-another-host'):
            self.sync()
        self.assertEqual(self.tracked.read_text(encoding='utf-8'), snapshot)

    def test_sync_extends_a_snapshot_it_contains(self):
        live = text(row('shared'), row('local'))
        self.ledger.write_text(live, encoding='utf-8')
        self.tracked.write_text(text(row('shared')), encoding='utf-8')
        self.sync()
        self.assertEqual(self.tracked.read_text(encoding='utf-8'), live)


if __name__ == '__main__':
    unittest.main()
