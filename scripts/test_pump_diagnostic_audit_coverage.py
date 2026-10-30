#!/usr/bin/env python3
"""A diagnostic audit cannot attest to a report without paired logs."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_diagnostic_audit as gate  # noqa: E402


class DiagnosticAuditCoverageTests(unittest.TestCase):
    def audit(self, suites):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / 'report.json'
            output = root / 'audit.json'
            report.write_text(json.dumps({'suites': suites}), encoding='utf-8')
            argv = ['pump_diagnostic_audit.py', '--report', str(report), '--output', str(output)]
            with mock.patch.object(sys, 'argv', argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    return gate.main(), output.exists()
                except ValueError as error:
                    self.assertIn('no paired logs', str(error))
                    return None, output.exists()

    def test_report_without_paired_logs_is_rejected_without_a_receipt(self):
        for suites in ({},
                       {'suite': []},
                       {'suite': [{'name': 'case', 'result': 'passed'}]},
                       {'suite': [{'original': {'logs': []}, 'candidate': {'logs': []}}]}):
            with self.subTest(suites=suites):
                self.assertEqual(self.audit(suites), (None, False))

    def test_report_with_paired_logs_keeps_its_result(self):
        pair = {'original': {'logs': ['Program log: same']},
                'candidate': {'logs': ['Program log: same']}}
        self.assertEqual(self.audit({'suite': [pair]}), (False, True))


if __name__ == '__main__':
    unittest.main()
