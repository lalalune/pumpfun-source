#!/usr/bin/env python3
"""Triage JSON can be written when the output directory does not exist yet."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('window_triage', Path(__file__).with_name('triage.py'))
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)


class TriageReportTests(unittest.TestCase):
    def test_missing_parent_directory_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'current' / 'triage.json'
            triage.write_report(path, [{'start': '0x120'}])
            self.assertEqual(path.read_text(), '[\n {\n  "start": "0x120"\n }\n]')

    def test_existing_directory_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'triage.json'
            triage.write_report(path, [])
            triage.write_report(path, [])
            self.assertEqual(path.read_text(), '[]')


if __name__ == '__main__':
    unittest.main()
