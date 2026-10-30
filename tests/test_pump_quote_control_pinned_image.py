"""Real quote-control CLI image binding, input preservation and atomic publication.

Captured Pump is a diagnostic candidate, not a reconstructed build. All 491
cases retain the captured Global fixture and signed VM transactions.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'
SCRIPT = ROOT / 'scripts/pump_quote_control_differential.py'
DRIVER = r'''
import json, os, shutil, sys
from pathlib import Path
scripts, fixture_root, candidate, replacement, output, audit, mode = sys.argv[1:]
sys.path.insert(0, scripts)
import pump_quote_control_differential as module
module.ROOT = Path(fixture_root)
original = module.ROOT / 'evidence/original/pump/deployed.so'
returned = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'execute' and frame.f_code.co_filename == module.__file__:
        if isinstance(arg, dict):
            frame.f_locals['tx'].verify()
            returned.append({'signature_verified': True, 'error': arg.get('error')})
        if len(returned) == 2:
            if mode == 'mutate':
                shutil.copyfile(replacement, candidate)
                shutil.copyfile(replacement, original)
            elif mode == 'late-alias':
                Path(output).unlink(missing_ok=True)
                Path(output).symlink_to(candidate)
if mode == 'stage-failure':
    import pump_differential_output as publication
    def fail_replace(*args):
        raise OSError('controlled publication failure')
    publication.os.replace = fail_replace
sys.setprofile(hook)
sys.argv = [module.__file__, '--output', output]
if mode == 'original-only':
    sys.argv += ['--original-only', '--candidate', candidate]
else:
    sys.argv += ['--candidate', candidate]
old_umask = os.umask(0o022)
try:
    raise SystemExit(module.main())
finally:
    sys.setprofile(None)
    os.umask(old_umask)
    Path(audit).write_text(json.dumps(returned))
'''


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def receipt(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw)


class QuoteControlPinnedImageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='quote-control-binding-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        original = self.root / 'evidence/original/pump/deployed.so'
        original.parent.mkdir(parents=True)
        shutil.copyfile(ORIGINAL, original)
        self.original = original
        (self.root / 'evidence/original/pump_fees').symlink_to(OTHER.parent, target_is_directory=True)
        (self.root / 'evidence/dependencies').symlink_to(ROOT / 'evidence/dependencies', target_is_directory=True)
        self.candidate = self.root / 'candidate.so'
        shutil.copyfile(ORIGINAL, self.candidate)
        self.output = self.root / 'new/nested/receipt.json.gz'
        self.audit = self.root / 'audit.json'

    def run_cli(self, mode='normal', output=None):
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        result = subprocess.run(
            [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts'), str(self.root),
             str(self.candidate), str(OTHER), str(output or self.output), str(self.audit), mode],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120)
        return result

    def assert_full_signed_run(self, candidate=True):
        rows = json.loads(self.audit.read_text())
        self.assertEqual(len(rows), 982 if candidate else 491)
        self.assertTrue(all(row['signature_verified'] is True for row in rows))

    def test_both_images_stay_bound_after_first_pair(self):
        result = self.run_cli('mutate')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertEqual(digest(self.candidate), digest(OTHER))
        self.assertEqual(digest(self.original), digest(OTHER))
        report = receipt(self.output)
        self.assertEqual(report['original_sha256'], digest(ORIGINAL))
        self.assertEqual(report['candidate_sha256'], digest(ORIGINAL))
        self.assertEqual(report['cases'], 491)
        self.assertEqual(report['mismatches'], 0)
        self.assertTrue(all(row['matches'] is True for row in report['results']))
        self.assert_full_signed_run()

    def test_stable_wrong_candidate_reports_actual_mismatches(self):
        shutil.copyfile(OTHER, self.candidate)
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        report = receipt(self.output)
        self.assertEqual(report['candidate_sha256'], digest(OTHER))
        self.assertTrue(report['mismatches'])
        self.assertEqual(report['cases'], 491)
        self.assert_full_signed_run()

    def test_original_only_keeps_no_comparison_and_normal_file_mode(self):
        self.candidate.write_bytes(b'ignored candidate')
        result = self.run_cli('original-only')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        report = receipt(self.output)
        self.assertIsNone(report['candidate_sha256'])
        self.assertTrue(all('candidate' not in row and 'matches' not in row for row in report['results']))
        self.assert_full_signed_run(candidate=False)
        if os.name != 'nt':
            self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o644)
            self.assertEqual(stat.S_IMODE(self.output.parent.stat().st_mode), 0o755)
        self.assertEqual(list(self.output.parent.glob('.receipt.json.gz.*')), [])

    def test_public_candidate_and_original_aliases_are_rejected(self):
        symlink, hardlink = self.root / 'alias.so', self.root / 'hard.so'
        symlink.symlink_to(self.candidate)
        os.link(self.candidate, hardlink)
        for output in (self.candidate, symlink, hardlink, self.original):
            with self.subTest(output=output):
                shutil.copyfile(ORIGINAL, self.candidate)
                shutil.copyfile(ORIGINAL, self.original)
                result = self.run_cli(output=output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
                self.assertEqual(digest(self.candidate), digest(ORIGINAL))
                self.assertEqual(digest(self.original), digest(ORIGINAL))
                self.assertEqual(json.loads(self.audit.read_text()), [])

    def test_late_alias_does_not_overwrite_candidate(self):
        self.output.parent.mkdir(parents=True)
        result = self.run_cli('late-alias')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('report output aliases an input', result.stderr)
        self.assertTrue(self.output.is_symlink())
        self.assertEqual(digest(self.candidate), digest(ORIGINAL))
        self.assert_full_signed_run()
        self.assertEqual(list(self.output.parent.glob('.receipt.json.gz.*')), [])

    def test_vm_and_publication_failures_preserve_existing_receipt(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b'prior complete receipt')
        self.candidate.write_bytes(b'not an ELF')
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.output.read_bytes(), b'prior complete receipt')
        shutil.copyfile(ORIGINAL, self.candidate)
        result = self.run_cli('stage-failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('controlled publication failure', result.stderr)
        self.assertEqual(self.output.read_bytes(), b'prior complete receipt')
        self.assertEqual(list(self.output.parent.glob('.receipt.json.gz.*')), [])
        self.assert_full_signed_run()

    def test_direct_cli_full_suite_and_original_only_without_output(self):
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--candidate',
                                 str(self.candidate), '--output', str(self.output)],
                                env=environment, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertEqual(receipt(self.output)['cases'], 491)
        self.assertEqual(receipt(self.output)['mismatches'], 0)
        self.candidate.write_bytes(b'ignored candidate')
        before = self.output.read_bytes()
        result = subprocess.run([sys.executable, '-O', '-B', str(SCRIPT), '--original-only',
                                 '--candidate', str(self.candidate)], env=environment,
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertIn('491 cases, 0 mismatches', result.stdout)
        self.assertEqual(self.output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
