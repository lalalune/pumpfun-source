#!/usr/bin/env python3
"""A suite receipt that fails admission must not sit beside admitted receipts."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_validate_parallel as validator
import test_pump_validate_parallel as fixtures


class RejectedReceiptTests(fixtures.ParallelReportPublicationTests):
    def run_rejected(self, output):
        argv = ['pump_validate_parallel.py', '--candidate', str(self.candidate),
                '--source-directory', str(self.source),
                '--build-comparison', str(self.build_comparison),
                '--output', str(output), '--workers', '1']
        with mock.patch.object(validator, 'ROOT', self.root), \
                mock.patch.object(validator.base, 'SUITES', [('fixture', 'fixture.py')]), \
                mock.patch.object(validator.base, 'EXPECTED_CASES', {'fixture': 1}), \
                mock.patch.object(validator, 'validate_result',
                                  side_effect=AssertionError('receipt rejected')), \
                mock.patch.object(sys, 'argv', argv):
            validator.main()

    def test_rejected_receipt_is_kept_apart_from_admitted_names(self):
        output = self.root / 'reports/report.json'
        with self.assertRaisesRegex(RuntimeError, 'suite failure'):
            self.run_rejected(output)
        retained = output.with_name(output.name + '.suites')
        self.assertFalse((retained / 'fixture.json.gz').exists())
        failure = json.loads(output.with_name(output.name + '.failed.json').read_text())
        self.assertEqual(failure['completed_suites'], [])
        entry = failure['failed_suite_outputs']['fixture']
        self.assertEqual((self.root / entry['path']).read_bytes(), b'{"fixture": true}')
        self.assertEqual(entry['sha256'], hashlib.sha256(b'{"fixture": true}').hexdigest())
        self.assertIn('receipt rejected', entry['reason'])


if __name__ == '__main__':
    unittest.main()
