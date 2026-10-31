#!/usr/bin/env python3
"""Parallel validation reports keep the same umask mode as a direct write."""
import gzip
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_validate_parallel as validator


@unittest.skipIf(os.name == 'nt', 'POSIX permission bits')
class ParallelReportModeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='parallel-report-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)

    def publish(self, path, mask):
        previous = os.umask(mask)
        try:
            validator.publish_report(path, b'{}')
        finally:
            os.umask(previous)
        return stat.S_IMODE(path.stat().st_mode)

    def test_new_report_keeps_the_process_umask(self):
        for name in ('report.json', 'report.json.gz', 'report.json.failed.json'):
            for mask, mode in ((0o022, 0o644), (0o027, 0o640)):
                with self.subTest(name=name, mask=oct(mask)):
                    path = self.work / oct(mask) / name
                    self.assertEqual(self.publish(path, mask), mode)

    def test_replacement_keeps_the_process_umask(self):
        path = self.work / 'report.json'
        path.write_bytes(b'prior')
        path.chmod(0o600)
        self.assertEqual(self.publish(path, 0o022), 0o644)
        self.assertEqual(path.read_bytes(), b'{}')

    def test_gzip_payload_and_long_names_still_publish(self):
        path = self.work / ('r' * 200 + '.json.gz')
        validator.publish_report(path, b'{}')
        self.assertEqual(gzip.decompress(path.read_bytes()), b'{}')
        self.assertEqual(list(self.work.iterdir()), [path])

    def test_failed_replacement_keeps_the_prior_report(self):
        path = self.work / 'report.json'
        path.write_bytes(b'prior')
        with mock.patch.object(validator.os, 'replace', side_effect=OSError('refused')):
            with self.assertRaises(OSError):
                validator.publish_report(path, b'{}')
        self.assertEqual(path.read_bytes(), b'prior')
        self.assertEqual(list(self.work.iterdir()), [path])


if __name__ == '__main__':
    unittest.main()
