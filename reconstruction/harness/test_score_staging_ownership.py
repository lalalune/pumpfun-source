"""Supplemental real-filesystem publication checks; primary proof is full CLI."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

import score


class ScoreStagingOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        repo = Path(__file__).resolve().parents[2]
        self.receipt = (repo / 'reconstruction/pump-main/baseline/score.json').read_text(encoding='utf-8')

    def test_existing_pid_receipt_is_preserved_and_new_report_published(self):
        prior = self.root / f'.score-{os.getpid()}'
        prior.write_text(self.receipt, encoding='utf-8')
        output = self.root / 'score.json'
        score.write_report(output, self.receipt)
        self.assertEqual(prior.read_text(encoding='utf-8'), self.receipt)
        self.assertEqual(output.read_text(encoding='utf-8'), self.receipt)
        self.assertEqual(set(self.root.iterdir()), {prior, output})

    def test_simultaneous_same_process_publishers_keep_distinct_complete_reports(self):
        outputs = [self.root / f'score-{i}.json' for i in range(24)]
        with ThreadPoolExecutor(max_workers=8) as workers:
            list(workers.map(lambda output: score.write_report(output, self.receipt), outputs))
        for output in outputs:
            self.assertEqual(output.read_text(encoding='utf-8'), self.receipt)
            self.assertTrue(json.loads(output.read_text(encoding='utf-8'))['windows'])
        self.assertEqual(set(self.root.iterdir()), set(outputs))

    def test_real_publication_failure_cleans_only_owned_stage(self):
        output = self.root / 'occupied-directory'
        output.mkdir()
        sentinel = output / 'keep.json'
        sentinel.write_text(self.receipt, encoding='utf-8')
        prior = self.root / f'.score-{os.getpid()}'
        prior.write_text(self.receipt, encoding='utf-8')
        with self.assertRaises(OSError):
            score.write_report(output, self.receipt)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), self.receipt)
        self.assertEqual(prior.read_text(encoding='utf-8'), self.receipt)
        self.assertEqual(set(self.root.iterdir()), {prior, output})

    @unittest.skipIf(os.name == 'nt', 'POSIX umask semantics')
    def test_published_file_retains_plain_write_umask_mode(self):
        previous = os.umask(0o027)
        try:
            output = self.root / 'score.json'
            score.write_report(output, self.receipt)
        finally:
            os.umask(previous)
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o640)


if __name__ == '__main__':
    unittest.main()
