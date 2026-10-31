#!/usr/bin/env python3
"""Both log audits must refuse a report whose suites member is not a mapping.

pump_diagnostic_audit walked report['suites'] with .items(), so a JSON receipt
whose suites member was a list failed with an AttributeError traceback.
pump_strict_ordered_logs refused the same receipt with an unrelated coverage
message. Both now name the malformed member.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_diagnostic_audit as diagnostic  # noqa: E402
import pump_strict_ordered_logs as ordered  # noqa: E402


class AuditSuiteShapeTests(unittest.TestCase):
    def test_diagnostic_audit_refuses_a_non_mapping(self):
        with self.assertRaisesRegex(ValueError, 'report suites must be a mapping'):
            diagnostic.audit([])
        with self.assertRaisesRegex(ValueError, 'report suites must be a mapping'):
            diagnostic.audit('suites')
        result = diagnostic.audit({'suite': [{
            'original': {'logs': ['a']},
            'candidate': {'logs': ['a']},
        }]})
        self.assertEqual(result['log_bearing_cases'], 1)

    def test_diagnostic_audit_cli_names_the_malformed_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / 'report.json'
            report.write_text(json.dumps({'suites': []}), encoding='utf-8')
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/pump_diagnostic_audit.py'),
                 '--report', str(report), '--output', str(Path(temporary) / 'audit.json')],
                capture_output=True, text=True, timeout=120)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('report suites must be a mapping', result.stderr)

    def test_strict_ordered_audit_refuses_a_non_mapping(self):
        report = {'original_sha256': ordered.ORIGINAL, 'candidate_sha256': 'candidate',
                  'case_count': 1, 'suites': []}
        with self.assertRaisesRegex(ValueError, 'Report suites must be a mapping'):
            ordered.audit(report, 'candidate')


if __name__ == '__main__':
    unittest.main()

