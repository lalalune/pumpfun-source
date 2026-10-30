"""Malformed execution pairs must not disappear from ordered-log coverage."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import pump_strict_ordered_logs as gate


class LogCoverageTests(unittest.TestCase):
    def report(self):
        pair = {'original': {'logs': ['Program log: one']},
                'candidate': {'logs': ['Program log: one']}}
        return {'original_sha256': gate.ORIGINAL, 'candidate_sha256': 'a' * 64,
                'case_count': 1, 'suites': {'one': [pair]}}

    def test_complete_pair_is_accepted(self):
        self.assertEqual(gate.audit(self.report(), 'a' * 64)['case_pairs'], 1)

    def test_changed_logs_are_still_reported(self):
        report = self.report()
        report['suites']['one'][0]['candidate']['logs'].append('Program log: changed')
        self.assertEqual(gate.audit(report, 'a' * 64)['strict_ordered_log_mismatch_cases'], 1)

    def test_metadata_logs_and_compute_meter_exclusion(self):
        report = self.report()
        pair = report['suites']['one'][0]
        pair['candidate'] = {'metadata': {'logs': ['Program log: one',
            'Program 11111111111111111111111111111111 consumed 17 of 99 compute units']}}
        self.assertEqual(gate.audit(report, 'a' * 64)['strict_ordered_log_mismatch_cases'], 0)

    def test_orphan_execution_is_rejected(self):
        for side in ('original', 'candidate'):
            for missing in (None, [], 'unavailable'):
                with self.subTest(side=side, missing=missing):
                    report = self.report()
                    report['suites']['one'].append({side: {'logs': []},
                        ('candidate' if side == 'original' else 'original'): missing})
                    with self.assertRaises(ValueError):
                        gate.audit(report, 'a' * 64)

    def test_missing_side_is_rejected(self):
        report = self.report()
        report['suites']['one'].append({'original': {'logs': []}})
        with self.assertRaises(ValueError):
            gate.audit(report, 'a' * 64)

    def test_counts_must_be_integers_not_boolean_or_float(self):
        for value in (True, 1.0):
            report = self.report()
            report['case_count'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                gate.audit(report, 'a' * 64, 1)
        with self.assertRaises(ValueError):
            gate.audit(self.report(), 'a' * 64, True)


if __name__ == '__main__':
    unittest.main()
