#!/usr/bin/env python3
"""The two-curve build binding must accept a receipt beside an external candidate."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_tokenkeg_two_curve_differential as tool

SOURCES = {'programs/pump/src/lib.rs': '0' * 64}


def write_receipts(directory):
    candidate = directory / 'candidate.so'
    candidate.write_bytes(b'candidate bytes')
    report = directory / 'build-comparison.json'
    report.write_text(json.dumps({'source_sha256': SOURCES, 'comparison': {
        'candidate_sha256': tool.fixture.sha(candidate)}}), encoding='utf-8')
    (directory / 'build-attempt.json').write_text(json.dumps({
        'returncode': 0, 'source_unchanged': True, 'source_sha256': SOURCES,
        'source_after_sha256': SOURCES}), encoding='utf-8')
    return candidate, report


class ReportPathTests(unittest.TestCase):
    def binding(self, directory):
        candidate, report = write_receipts(directory)
        with mock.patch.object(tool, 'source_manifest', return_value=SOURCES):
            try:
                return report, tool.compiled_binding(candidate, report)
            except ValueError as error:
                self.fail(f'build receipt was refused by its path: {error}')

    def test_external_receipt_is_bound_by_its_full_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            report, binding = self.binding(Path(temporary).resolve())
            self.assertEqual(binding['report'], str(report))
            self.assertEqual(binding['report_sha256'], tool.fixture.sha(report))

    def test_repository_receipt_keeps_its_relative_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            with mock.patch.object(tool, 'ROOT', directory.parent):
                report, binding = self.binding(directory)
            self.assertEqual(binding['report'], str(report.relative_to(directory.parent)))


if __name__ == '__main__':
    unittest.main()
