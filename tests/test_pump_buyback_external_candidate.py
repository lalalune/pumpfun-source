#!/usr/bin/env python3
"""Replay actual captured ELFs through internal and external candidate paths."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_buyback_recipient_differential.py'
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
OTHER = ROOT / 'evidence/original/mayhem/deployed.so'

class BuybackExternalCandidateTests(unittest.TestCase):
    def run_replay(self, candidate, output):
        completed = subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(candidate), '--output', str(output)],
            cwd=ROOT, capture_output=True, text=True, timeout=180)
        self.assertTrue(output.is_file(), completed.stdout[-2000:] + completed.stderr[-2000:])
        return completed, json.loads(output.read_text(encoding='utf-8'))

    def test_optimized_python_refuses_to_drop_input_checks(self):
        for flag in ('-O', '-OO'):
            with self.subTest(flag=flag):
                completed = subprocess.run(
                    [sys.executable, flag, str(SCRIPT), '--help'],
                    cwd=ROOT, capture_output=True, text=True, timeout=30)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn('Normal Python is required', completed.stderr)

    def test_symlink_retarget_cannot_switch_the_admitted_input(self):
        driver = r"""
import runpy, sys
from pathlib import Path
script, link, replacement, output = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
returned = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'execute' and frame.f_code.co_filename.endswith('pump_validate_config_admin.py'):
        returned.append(1)
        if len(returned) == 2:
            sys.setprofile(None)
            Path(link).unlink()
            Path(link).symlink_to(replacement)
sys.setprofile(hook)
sys.argv = [script, '--candidate', link, '--output', output]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    sys.setprofile(None)
    if len(returned) < 2:
        raise RuntimeError('did not retarget candidate')
"""
        with tempfile.TemporaryDirectory(prefix='buyback-link-') as temporary:
            temporary = Path(temporary).resolve()
            admitted = temporary / 'admitted.so'
            link = temporary / 'candidate.so'
            output = temporary / 'report.json'
            shutil.copyfile(ORIGINAL, admitted)
            link.symlink_to(admitted)
            completed = subprocess.run(
                [sys.executable, '-B', '-c', driver, str(SCRIPT), str(link), str(OTHER), str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=180)
            self.assertEqual(completed.returncode, 0, completed.stdout[-2000:] + completed.stderr[-2000:])
            self.assertEqual(link.resolve(), OTHER.resolve())
            report = json.loads(output.read_text(encoding='utf-8'))
            digest = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
            self.assertEqual(report['candidate_sha256'], digest)
            self.assertEqual(report['bound_inputs_sha256'][str(admitted)], digest)
            self.assertEqual(report['mismatches'], [])

    def test_external_path_preserves_cases_bindings_and_negative_detection(self):
        with tempfile.TemporaryDirectory(prefix='buyback-candidate-') as temporary:
            temporary = Path(temporary).resolve()
            self.assertFalse(temporary.is_relative_to(ROOT))
            candidate = temporary / 'candidate.so'
            shutil.copyfile(ORIGINAL, candidate)
            internal, control = self.run_replay(ORIGINAL, temporary / 'internal.json')
            external, result = self.run_replay(candidate, temporary / 'external.json')
            self.assertEqual(internal.returncode, 0, internal.stderr[-2000:])
            self.assertEqual(external.returncode, 0, external.stderr[-2000:])
            self.assertEqual(result['case_count'], 42)
            self.assertEqual(result['cases'], control['cases'])
            self.assertEqual(result['mismatches'], [])
            digest = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()
            self.assertEqual(result['bound_inputs_sha256'][str(candidate)], digest)
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), digest)
            self.assertEqual(control['bound_inputs_sha256'][ORIGINAL.relative_to(ROOT).as_posix()], digest)
            wrong = temporary / 'wrong.so'
            shutil.copyfile(OTHER, wrong)
            negative, rejected = self.run_replay(wrong, temporary / 'negative.json')
            self.assertNotEqual(negative.returncode, 0)
            self.assertEqual(rejected['case_count'], 42)
            self.assertTrue(rejected['mismatches'])

if __name__ == '__main__':
    unittest.main()
