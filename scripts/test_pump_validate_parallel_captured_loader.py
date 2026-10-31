#!/usr/bin/env python3
"""A real captured-loader receipt must pass the parallel validator's admission."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_validate_parallel as validator  # noqa: E402
from source_manifest_guard import strict_manifest  # noqa: E402

CAPTURED = ('capture.json', 'program-account.bin', 'programdata-account.bin', 'deployed.so')
SUITE = '''import argparse, json
from pathlib import Path
import pump_captured_loader as loader
from solders.litesvm import LiteSVM
parser = argparse.ArgumentParser()
parser.add_argument('--candidate')
parser.add_argument('--output', type=Path)
args = parser.parse_args()
LiteSVM().add_program_from_file(loader.PROGRAM, args.candidate)
args.output.write_text(json.dumps({'fixture': True}))
'''


class CapturedLoaderAdmissionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / 'repo'
        self.scripts = self.root / 'scripts'
        self.scripts.mkdir(parents=True)
        # Run the real wrapper and loader; only the suite list is a fixture.
        for name in ('pump_with_captured_loader.py', 'pump_captured_loader.py', 'probe_report.py'):
            shutil.copyfile(SCRIPTS / name, self.scripts / name)
        (self.scripts / 'pump_diagnostic_audit.py').write_text('')
        (self.scripts / 'fixture.py').write_text(SUITE)
        evidence = self.root / 'evidence/original/pump'
        evidence.mkdir(parents=True)
        for name in CAPTURED:
            shutil.copyfile(SCRIPTS.parent / 'evidence/original/pump' / name, evidence / name)
        self.candidate = self.root / 'candidate.so'
        shutil.copyfile(evidence / 'deployed.so', self.candidate)
        self.source = self.root / 'source'
        (self.source / 'src').mkdir(parents=True)
        (self.source / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n[workspace]\n')
        (self.source / 'Cargo.lock').write_text('version = 3\n')
        (self.source / 'src/lib.rs').write_text('pub fn fixture() {}\n')
        self.build_comparison = self.root / 'build-comparison.json'
        self.build_comparison.write_text(json.dumps({
            'returncode': 0,
            'source_unchanged': True,
            'comparison': {'candidate_sha256': hashlib.sha256(self.candidate.read_bytes()).hexdigest()},
            'source_sha256': strict_manifest(self.source, self.source, self.root, cwd=self.source),
        }))
        self.output = self.root / 'reports/report.json'

    def run_validator(self):
        argv = ['pump_validate_parallel.py', '--candidate', str(self.candidate),
                '--source-directory', str(self.source),
                '--build-comparison', str(self.build_comparison),
                '--output', str(self.output), '--workers', '1', '--captured-loader']
        diagnostics = {'mismatches': [], 'log_bearing_cases': 1}
        with mock.patch.object(validator, 'ROOT', self.root), \
                mock.patch.object(validator.base, 'SUITES', [('fixture', 'fixture.py')]), \
                mock.patch.object(validator.base, 'EXPECTED_CASES', {'fixture': 1}), \
                mock.patch.object(validator, 'validate_result', return_value=1), \
                mock.patch.object(validator, 'audit', return_value=diagnostics), \
                mock.patch.object(sys, 'argv', argv):
            return validator.main()

    def test_receipt_from_the_real_wrapper_is_admitted(self):
        try:
            self.assertFalse(self.run_validator())
        except RuntimeError:
            failure = json.loads(self.output.with_name(self.output.name + '.failed.json').read_text())
            self.fail(failure['errors'][0]['error'])
        report = json.loads(self.output.read_text())
        self.assertEqual(report['loader_receipts']['fixture']['load_count'], 1)
        self.assertIn(str(self.scripts / 'probe_report.py'), report['bound_files_sha256'])


if __name__ == '__main__':
    unittest.main()
