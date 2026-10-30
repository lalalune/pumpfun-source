#!/usr/bin/env python3
"""Exercise final report publication in the parallel Pump validator."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import pump_validate_parallel as validator
from source_manifest_guard import strict_manifest


class ParallelReportPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'repo'
        self.scripts = self.root / 'scripts'
        self.scripts.mkdir(parents=True)
        self.original = self.root / 'evidence/original/pump/deployed.so'
        self.original.parent.mkdir(parents=True)
        self.original.write_bytes(b'original')
        self.candidate = self.root / 'candidate.so'
        self.candidate.write_bytes(b'candidate')
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'src').mkdir()
        (self.source / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n[workspace]\n')
        (self.source / 'Cargo.lock').write_text('version = 3\n')
        (self.source / 'src/lib.rs').write_text('pub fn fixture() {}\n')
        self.build_comparison = self.root / 'build-comparison.json'
        self.build_comparison.write_text(json.dumps({
            'returncode': 0,
            'source_unchanged': True,
            'comparison': {
                'candidate_sha256': hashlib.sha256(
                    self.candidate.read_bytes()).hexdigest(),
            },
            'source_sha256': strict_manifest(self.source, self.source, self.root, cwd=self.source),
        }))
        (self.scripts / 'pump_diagnostic_audit.py').write_text('')
        self.suite = self.scripts / 'fixture.py'
        self.suite.write_text(
            'import argparse, json\n'
            'from pathlib import Path\n'
            'parser = argparse.ArgumentParser()\n'
            "parser.add_argument('--candidate')\n"
            "parser.add_argument('--output', type=Path)\n"
            'args = parser.parse_args()\n'
            "args.output.write_text(json.dumps({'fixture': True}))\n"
        )

    def run_validator(self, output):
        argv = [
            'pump_validate_parallel.py',
            '--candidate', str(self.candidate),
            '--source-directory', str(self.source),
            '--build-comparison', str(self.build_comparison),
            '--output', str(output),
            '--workers', '1',
        ]
        diagnostics = {'mismatches': [], 'log_bearing_cases': 1}
        with mock.patch.object(validator, 'ROOT', self.root), \
                mock.patch.object(validator.base, 'SUITES', [
                    ('fixture', 'fixture.py'),
                ]), \
                mock.patch.object(validator.base, 'EXPECTED_CASES', {
                    'fixture': 1,
                }), \
                mock.patch.object(validator, 'validate_result', return_value=1), \
                mock.patch.object(validator, 'audit', return_value=diagnostics), \
                mock.patch.object(sys, 'argv', argv):
            return validator.main()

    def test_json_output_is_plain_json(self):
        output = self.root / 'reports/report.json'
        self.assertFalse(self.run_validator(output))
        self.assertEqual(json.loads(output.read_bytes())['case_count'], 1)

    def test_malformed_loader_completion_marker_is_not_admitted(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'loader.json'
            for flag in (0, 1, None, "false", "true"):
                with self.subTest(flag=flag):
                    path.write_text(json.dumps({'loads': [{}], 'ok': flag}))
                    with self.assertRaisesRegex(AssertionError, 'invalid loader completion marker'):
                        validator.validate_loader_receipt('suite', path, path, path, path, [])

    def test_failed_loader_receipt_is_not_admitted(self):
        # A receipt written after a failed harness run carries ok:false and
        # the failure text; admission must reject it before binding checks,
        # while receipts sealed before the marker existed stay admissible.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / 'suite.py'
            script.write_text('pass\n', encoding='utf-8')
            receipt = root / 'loader.json'
            receipt.write_text(json.dumps({
                'loads': [{'elf_sha256': '0' * 64}],
                'ok': False,
                'error': 'RuntimeError: fixture exploded',
                'harness': str(script.resolve()),
            }), encoding='utf-8')
            with self.assertRaisesRegex(AssertionError, 'loader harness run failed'):
                validator.validate_loader_receipt(
                    'suite', receipt, script, script, script, [])
            legacy = root / 'legacy-loader.json'
            payload = json.loads(receipt.read_text())
            payload.pop('ok')
            payload.pop('error')
            legacy.write_text(json.dumps(payload), encoding='utf-8')
            # The legacy receipt gets past the new marker check and fails
            # later on its (absent) input binding, not on the marker.
            with self.assertRaises((AssertionError, KeyError)) as raised:
                validator.validate_loader_receipt(
                    'suite', legacy, script, script, script, [])
            self.assertNotIn('loader harness run failed', str(raised.exception))

    def test_bound_inputs_are_rejected_before_worker_publication(self):
        for output in (self.candidate, self.build_comparison, self.suite):
            with self.subTest(output=output):
                before = output.read_bytes()
                with self.assertRaisesRegex(ValueError, 'validation output aliases a bound input'):
                    self.run_validator(output)
                self.assertEqual(output.read_bytes(), before)
                self.assertFalse(output.with_name(output.name + '.suites').exists())
                self.assertFalse(output.with_name(output.name + '.failed.json').exists())

    def test_gz_output_remains_gzip(self):
        output = self.root / 'reports/report.json.gz'
        self.assertFalse(self.run_validator(output))
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['case_count'], 1)

    def test_failed_final_write_never_publishes_partial_json(self):
        output = self.root / 'reports/report.json'

        with mock.patch('os.fsync', side_effect=OSError(
                'injected durability failure')):
            with self.assertRaisesRegex(OSError, 'injected durability failure'):
                self.run_validator(output)

        self.assertFalse(output.exists())
        self.assertEqual(list(output.parent.glob('.' + output.name + '.*.tmp')), [])

    def test_failed_publication_preserves_prior_report(self):
        output = self.root / 'reports/report.json.gz'
        output.parent.mkdir(parents=True)
        prior = b'previous valid report\n'
        output.write_bytes(prior)

        with mock.patch('os.replace', side_effect=OSError(
                'injected publication failure')):
            with self.assertRaisesRegex(OSError,
                                        'injected publication failure'):
                self.run_validator(output)

        self.assertEqual(output.read_bytes(), prior)
        self.assertEqual(list(output.parent.glob('.' + output.name + '.*.tmp')), [])


if __name__ == '__main__':
    unittest.main()
