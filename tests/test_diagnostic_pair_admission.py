"""Malformed supplied outcomes cannot disappear from a retained-log audit."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'research/runtime-diagnostic-pair-admission-20261101/probe.py'


class DiagnosticPairAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='test-diagnostic-pairs-')
        cls.addClassCleanup(temporary.cleanup)
        cls.summaries = []
        for optimized in (False, True):
            output = Path(temporary.name) / str(optimized)
            command = [sys.executable, '-B', str(PROBE), '--repo', str(ROOT), '--output', str(output)]
            if optimized:
                command.append('--optimize')
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=90)
            if completed.returncode:
                raise RuntimeError(completed.stdout + completed.stderr)
            cls.summaries.append(json.loads((output / 'results.json').read_text(encoding='utf-8')))

    def test_malformed_outcomes_and_missing_log_sources_reject_before_publication(self):
        for summary in self.summaries:
            for row in summary['results']:
                if row['kind'] in ('malformed_outcome', 'incomplete_logs'):
                    with self.subTest(optimized=summary['optimized_children'], scenario=row['scenario'], gzip=row['gzip_input']):
                        self.assertNotEqual(row['returncode'], 0)
                        self.assertFalse(row['published'])
                        self.assertTrue(row['rejection_names_malformed_side'] if row['kind'] == 'malformed_outcome'
                                        else row['rejection_names_missing_side'])

    def test_complete_authentic_controls_retain_their_actual_diagnostics(self):
        for summary in self.summaries:
            for row in summary['results']:
                if row['kind'] in ('complete', 'mismatch'):
                    with self.subTest(scenario=row['scenario']):
                        mismatch = row['kind'] == 'mismatch'
                        self.assertEqual(row['returncode'], int(mismatch))
                        self.assertTrue(row['published'])
                        self.assertEqual(row['log_bearing_cases'], 50)
                        self.assertEqual(row['mismatches'], int(mismatch))

    def test_optional_logs_keep_their_existing_exclusion(self):
        for summary in self.summaries:
            for row in summary['results']:
                if row['kind'] in ('optional_logs', 'optional_outcome'):
                    with self.subTest(scenario=row['scenario']):
                        self.assertEqual(row['returncode'], 0)
                        self.assertTrue(row['published'])
                        self.assertEqual(row['log_bearing_cases'], 49)
                        self.assertEqual(row['mismatches'], 0)

    def test_inputs_remain_unchanged_and_no_staging_files_survive(self):
        for summary in self.summaries:
            self.assertEqual(summary['retained_cases'], 50)
            self.assertEqual(summary['new_vm_executions'], 0)
            self.assertEqual(len(summary['results']), 32)
            self.assertTrue(summary['source_unchanged'])
            for row in summary['results']:
                self.assertTrue(row['input_unchanged'])
                self.assertEqual(row['staging_files'], [])


if __name__ == '__main__':
    unittest.main()
