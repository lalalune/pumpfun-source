"""Ledger copy failures must preserve existing snapshots and permit retry."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import log_attempt


class LedgerPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / 'live/ATTEMPTS.jsonl'
        self.tracked = self.root / 'tracked.jsonl'
        self.tracked.write_bytes(b'{"dedupe_key":"first"}\n')
        self.globals = patch.multiple(log_attempt, LEDGER=self.ledger,
                                     LOCK=self.ledger.with_name('.attempts.lock'), TRACKED=self.tracked)
        self.globals.start()
        self.addCleanup(self.globals.stop)

    @staticmethod
    def interrupted_copy(source, destination):
        Path(destination).write_bytes(b'{"partial":')
        raise OSError('simulated interrupted copy')

    def test_seed_failure_does_not_leave_a_poisoned_live_ledger(self):
        with patch.object(log_attempt.shutil, 'copyfile', side_effect=self.interrupted_copy):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                log_attempt.locked(lambda rows: rows)
        self.assertFalse(self.ledger.exists())
        self.assertEqual(list(self.ledger.parent.glob('.attempts-*.tmp')), [])
        self.assertEqual(log_attempt.locked(lambda rows: rows), [{'dedupe_key': 'first'}])

    def sync(self, destination):
        with patch.object(sys, 'argv', ['log_attempt.py', 'sync', '--to', str(destination)]), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            log_attempt.main()
        return json.loads(output.getvalue())

    def test_sync_failure_keeps_prior_snapshot(self):
        log_attempt.locked(lambda rows: rows)
        destination = self.root / 'snapshot.jsonl'
        destination.write_bytes(b'prior snapshot\n')
        with patch.object(log_attempt.shutil, 'copyfile', side_effect=self.interrupted_copy):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                self.sync(destination)
        self.assertEqual(destination.read_bytes(), b'prior snapshot\n')
        self.assertEqual(self.ledger.read_bytes(), self.tracked.read_bytes())
        self.assertEqual(list(self.root.glob('.attempts-*.tmp')), [])

    def test_success_preserves_exact_bytes_and_reports_digest(self):
        destination = self.root / 'nested/snapshot.jsonl'
        result = self.sync(destination)
        self.assertEqual(destination.read_bytes(), self.tracked.read_bytes())
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['sha256'], log_attempt.hashlib.sha256(destination.read_bytes()).hexdigest())

    def test_replace_failure_preserves_old_destination(self):
        destination = self.root / 'snapshot.jsonl'
        destination.write_bytes(b'prior')
        with patch.object(log_attempt.os, 'replace', side_effect=OSError('replace failed')):
            with self.assertRaisesRegex(OSError, 'replace failed'):
                log_attempt.atomic_copy(self.tracked, destination)
        self.assertEqual(destination.read_bytes(), b'prior')
        self.assertEqual(list(self.root.glob('.attempts-*.tmp')), [])

    def test_sync_to_live_ledger_does_not_destroy_it(self):
        result = self.sync(self.ledger)
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(self.ledger.read_bytes(), self.tracked.read_bytes())


if __name__ == '__main__':
    unittest.main()
