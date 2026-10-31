#!/usr/bin/env python3
"""A failed second report must not leave the first one regenerated.

analyze.publish_reports stages both reports and then replaces each destination
in turn. An interruption between the two replaces used to leave
binary-analysis.json from the new run beside interface-inventory.json from the
previous one, and the next reader has no way to tell the pair apart.
"""
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze  # noqa: E402


class AnalyzeReportPairTests(unittest.TestCase):
    def paths(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        return root, root / 'binary-analysis.json', root / 'interface-inventory.json'

    def test_pair_is_published_together(self):
        root, first, second = self.paths()
        analyze.publish_reports([(first, 'new binary\n'), (second, 'new inventory\n')])
        self.assertEqual(first.read_bytes(), b'new binary\n')
        self.assertEqual(second.read_bytes(), b'new inventory\n')
        self.assertEqual(sorted(path.name for path in root.iterdir()),
                         ['binary-analysis.json', 'interface-inventory.json'])

    def test_failed_second_replace_restores_the_first(self):
        root, first, second = self.paths()
        first.write_bytes(b'old binary\n')
        second.write_bytes(b'old inventory\n')
        real_replace = os.replace
        calls = []

        def replace(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError('second replace failed')
            real_replace(source, destination)

        with mock.patch.object(analyze.os, 'replace', replace):
            with self.assertRaisesRegex(OSError, 'second replace failed'):
                analyze.publish_reports([(first, 'new binary\n'), (second, 'new inventory\n')])
        self.assertEqual(first.read_bytes(), b'old binary\n')
        self.assertEqual(second.read_bytes(), b'old inventory\n')
        self.assertEqual(sorted(path.name for path in root.iterdir()),
                         ['binary-analysis.json', 'interface-inventory.json'])

    def test_failed_second_replace_removes_a_first_publication(self):
        root, first, second = self.paths()
        real_replace = os.replace
        calls = []

        def replace(source, destination):
            calls.append(destination)
            if len(calls) == 2:
                raise OSError('second replace failed')
            real_replace(source, destination)

        with mock.patch.object(analyze.os, 'replace', replace):
            with self.assertRaisesRegex(OSError, 'second replace failed'):
                analyze.publish_reports([(first, 'new binary\n'), (second, 'new inventory\n')])
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())


if __name__ == '__main__':
    unittest.main()
