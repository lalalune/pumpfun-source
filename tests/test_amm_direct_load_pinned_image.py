"""Direct-loading PumpSwap differentials execute and report one candidate image.

boost, migration_create and creator_reassignment_cto load the candidate path
again for every case and hash the path when writing the report. Each test runs
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
DRIVER = r'''
import runpy, shutil, sys
script, candidate, other, *argv = sys.argv[1:]
sys.path.insert(0, str(__import__('pathlib').Path(script).parent))
swapped = []
def hook(frame, event, arg):
    if event != 'return' or swapped or frame.f_code.co_name not in ('boost', 'run_migration', 'run_cto'):
        return
    if frame.f_locals.get('candidate') or frame.f_locals.get('binary'):
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

class DirectLoadPinnedImageTest(unittest.TestCase):
    def run_swapped(self, name):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'candidate.so'
            output = Path(tmp) / 'report.json'
            shutil.copyfile(ORIGINAL, candidate)
            script = ROOT / 'scripts' / f'pump_amm_{name}_differential.py'
            proc = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(script), str(candidate), str(OTHER),
                 '--candidate', str(candidate), '--output', str(output)],
                cwd=ROOT, capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(sha(candidate), sha(OTHER), 'candidate was not replaced')
            self.assertEqual(proc.returncode, 0, proc.stdout[-2000:] + proc.stderr[-2000:])
            report = json.loads(output.read_text())
        self.assertEqual(report['candidate_sha256'], sha(ORIGINAL))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertEqual(report['mismatches'], [])

    def test_boost(self):
        self.run_swapped('boost')

    def test_migration_create(self):
        self.run_swapped('migration_create')

    def test_creator_reassignment_cto(self):
        self.run_swapped('creator_reassignment_cto')

if __name__ == '__main__':
    unittest.main()
