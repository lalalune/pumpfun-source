"""The Fees codec CLI loads and reports one image for original/candidate/baseline."""
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
SCRIPT = ROOT / 'scripts/fees_external_codec_differential.py'
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
OTHER = ROOT / 'evidence/original/mayhem/deployed.so'
DRIVER = r'''
import sys, shutil
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import fees_external_codec_differential as codec
original, candidate, baseline, other, output = sys.argv[2:]
codec.ORIGINAL = Path(original)
returns = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'run' and frame.f_code.co_filename.endswith('fees_sharing_create_differential.py'):
        returns.append(1)
        if len(returns) == 3:
            sys.setprofile(None)
            for path in (original, candidate, baseline):
                shutil.copyfile(other, path)
sys.setprofile(hook)
sys.argv = [str(codec.__file__), '--candidate', candidate, '--baseline', baseline, '--output', output]
try:
    codec.main()
finally:
    sys.setprofile(None)
    if len(returns) < 3:
        raise RuntimeError('first original/candidate/baseline case did not run')
'''

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class FeesExternalCodecPinnedImageTests(unittest.TestCase):
    def test_all_images_remain_pinned_after_source_paths_change(self):
        with tempfile.TemporaryDirectory(prefix='fees-codec-images-') as directory:
            directory = Path(directory)
            images = [directory / name for name in ('original.so', 'candidate.so', 'baseline.so')]
            for path in images:
                shutil.copyfile(ORIGINAL, path)
            output = directory / 'receipt.json'
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts'),
                 *map(str, images), str(OTHER), str(output)], cwd=ROOT,
                capture_output=True, text=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
            for path in images:
                self.assertEqual(sha(path), sha(OTHER), 'input path was not replaced')
            report = json.loads(output.read_text(encoding='utf-8'))
            for field in ('original_sha256', 'candidate_sha256', 'baseline_sha256'):
                self.assertEqual(report[field], sha(ORIGINAL))
            self.assertEqual(report['case_count'], 9)
            self.assertEqual(report['mismatches'], [])
            for row in report['cases']:
                self.assertEqual(row['baseline_errors'], row['original_errors'])

    def test_normal_wrong_candidate_still_produces_mismatches(self):
        with tempfile.TemporaryDirectory(prefix='fees-codec-negative-') as directory:
            output = Path(directory) / 'receipt.json'
            environment = dict(os.environ)
            environment.pop('PYTHONOPTIMIZE', None)
            result = subprocess.run(
                [sys.executable, '-B', str(SCRIPT), '--candidate', str(OTHER), '--output', str(output)],
                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(output.is_file(), result.stdout[-2000:] + result.stderr[-2000:])
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['candidate_sha256'], sha(OTHER))
            self.assertEqual(report['case_count'], 9)
            self.assertTrue(report['mismatches'])

if __name__ == '__main__':
    unittest.main()
