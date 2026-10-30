"""Exercise the real exact-quote CLI with replaced and counterfactual images.

Captured Pump bytes are a diagnostic candidate here, not a reconstructed build.
Every generated case and the normal signed VM transaction path remain enabled.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'
DRIVER = r'''
import sys, shutil
from pathlib import Path
scripts, fixture_root, candidate, replacement, output, mode = sys.argv[1:]
sys.path.insert(0, scripts)
import pump_exact_quote_differential as module
module.f.R = Path(fixture_root)
original = module.f.R / 'evidence/original/pump/deployed.so'
returned = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'run' and frame.f_code.co_filename == module.__file__:
        returned.append(1)
        if len(returned) == 2:
            sys.setprofile(None)
            shutil.copyfile(replacement, original)
            shutil.copyfile(replacement, candidate)
if mode == 'mutate':
    sys.setprofile(hook)
sys.argv = [module.__file__, '--output', output]
if mode != 'original-only':
    sys.argv += ['--candidate', candidate]
try:
    module.main()
finally:
    sys.setprofile(None)
    if mode == 'mutate' and len(returned) < 2:
        raise RuntimeError('the first original/candidate pair did not complete')
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ExactQuotePinnedImageTests(unittest.TestCase):
    def staged_run(self, mode):
        temporary = tempfile.TemporaryDirectory(prefix='exact-quote-binding-')
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        original = directory / 'evidence/original/pump/deployed.so'
        original.parent.mkdir(parents=True)
        shutil.copyfile(ORIGINAL, original)
        (directory / 'evidence/original/pump_fees').symlink_to(OTHER.parent, target_is_directory=True)
        (directory / 'evidence/dependencies').symlink_to(ROOT / 'evidence/dependencies', target_is_directory=True)
        candidate = directory / 'candidate.so'
        shutil.copyfile(OTHER if mode == 'wrong' else ORIGINAL, candidate)
        output = directory / 'receipt.json.gz'
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        result = subprocess.run(
            [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts'), str(directory),
             str(candidate), str(OTHER), str(output), mode],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180,
        )
        return result, output, original, candidate

    def check_signed_cases(self, report, candidate):
        self.assertGreater(report['case_count'], 1)
        self.assertEqual(report['case_count'], len(report['cases']))
        for row in report['cases']:
            self.assertTrue(row['original']['signature_verified'])
            if candidate:
                self.assertTrue(row['candidate']['signature_verified'])

    def test_original_and_candidate_keep_first_image_after_pair(self):
        result, output, original, candidate = self.staged_run('mutate')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assertEqual(sha(original), sha(OTHER))
        self.assertEqual(sha(candidate), sha(OTHER))
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertEqual(report['candidate_sha256'], sha(ORIGINAL))
        self.assertEqual(report['mismatches'], [])
        self.assertTrue(all(row['match'] is True for row in report['cases']))
        self.check_signed_cases(report, candidate=True)

    def test_stable_wrong_candidate_produces_real_mismatches(self):
        result, output, _, _ = self.staged_run('wrong')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output.is_file(), result.stderr[-2000:])
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertEqual(report['candidate_sha256'], sha(OTHER))
        self.assertTrue(report['mismatches'])
        self.check_signed_cases(report, candidate=True)

    def test_original_only_still_reports_no_comparison(self):
        result, output, _, _ = self.staged_run('original-only')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertIsNone(report['candidate_sha256'])
        self.assertEqual(report['mismatches'], [])
        self.assertTrue(all(row['candidate'] is None and row['match'] is None for row in report['cases']))
        self.check_signed_cases(report, candidate=False)


if __name__ == '__main__':
    unittest.main()
