"""acquire_harness PumpSwap callers execute and report one candidate image.

extend and incentives pass the candidate path to
acquire_harness for every case, which reloads changed bytes, and hash the path
when writing the report. Each test runs
the real CLI with a candidate that is replaced by another image after the first
candidate case; the run must still execute and report only the first bytes.
"""
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
ORIGINAL = ROOT / 'evidence/original/pump_amm/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'

# Swap the candidate file once the first candidate case returns.
# runpy compiles the script under the path it is given, so co_filename matches.
DRIVER = r'''
import runpy, shutil, sys
script, candidate, other, *argv = sys.argv[1:]
sys.path.insert(0, str(__import__('pathlib').Path(script).parent))
swapped = []
returns = []
def hook(frame, event, arg):
    if event != 'return' or swapped or frame.f_code.co_name not in ('run', 'extend'):
        return
    if frame.f_code.co_filename != script:
        return
    # Each suite runs the original, then the candidate, per case.
    returns.append(1)
    if len(returns) == 2:
        shutil.copyfile(other, candidate)
        swapped.append(1)
sys.setprofile(hook)
sys.argv = [script, *argv]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    sys.setprofile(None)
    if not swapped:
        sys.exit('candidate was never swapped')
'''

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class AcquireCallerPinnedImageTest(unittest.TestCase):
    def run_swapped(self, name, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'candidate.so'
            output = Path(tmp) / 'report.json'
            shutil.copyfile(ORIGINAL, candidate)
            script = ROOT / 'scripts' / f'pump_amm_{name}_differential.py'
            proc = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(script), str(candidate), str(OTHER),
                 '--candidate', str(candidate), '--output', str(output), *extra],
                cwd=ROOT, capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(sha(candidate), sha(OTHER), 'candidate was not replaced')
            self.assertEqual(proc.returncode, 0, proc.stdout[-2000:] + proc.stderr[-2000:])
            report = json.loads(output.read_text())
        self.assertEqual(report['candidate_sha256'], sha(ORIGINAL))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertEqual(report['mismatches'], [])

    def test_extend(self):
        self.run_swapped('extend')

    def test_incentives_sync(self):
        self.run_swapped('incentives', '--family', 'sync')

if __name__ == '__main__':
    unittest.main()
