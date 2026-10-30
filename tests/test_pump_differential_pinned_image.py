"""Eight Pump differential CLIs execute and report one candidate image per run.

Each real CLI continues using the initially admitted program bytes after its
candidate path is replaced following the first candidate case.
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

# Swap the candidate file once the first candidate case returns.
# runpy compiles the script under the path it is given, so co_filename matches.
DRIVER = r'''
import runpy, shutil, sys
script, candidate, other, *argv = sys.argv[1:]
sys.path.insert(0, str(__import__('pathlib').Path(script).parent))
swapped = []
returns = []
def hook(frame, event, arg):
    if event != 'return' or swapped or frame.f_code.co_name not in ('run',):
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

class PumpDifferentialPinnedImageTest(unittest.TestCase):
    def run_swapped(self, name, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'candidate.so'
            output = Path(tmp) / 'report.json.gz'
            shutil.copyfile(ORIGINAL, candidate)
            script = ROOT / 'scripts' / f'pump_{name}_differential.py'
            proc = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(script), str(candidate), str(OTHER),
                 '--candidate', str(candidate), '--output', str(output), *extra],
                cwd=ROOT, capture_output=True, text=True, timeout=180,
                env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            self.assertEqual(proc.returncode, 0, proc.stdout[-2000:] + proc.stderr[-2000:])
            self.assertEqual(sha(candidate), sha(OTHER), 'candidate was not replaced')
            data = output.read_bytes()
            report = json.loads(gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data)
        self.assertEqual(report['candidate_sha256'], sha(ORIGINAL))
        self.assertEqual(report['original_sha256'], sha(ORIGINAL))
        self.assertEqual(report['mismatches'], [])

    def test_extend(self):
        self.run_swapped('extend')

    def test_create(self):
        self.run_swapped('create')

    def test_create_v2(self):
        self.run_swapped('create_v2')

    def test_create_quote(self):
        self.run_swapped('create_quote')

    def test_volume_sync(self):
        self.run_swapped('volume_sync')

    def test_incentives_admin(self):
        self.run_swapped('incentives_admin')

    def test_create_control(self):
        self.run_swapped('create_control')

    def test_idl_authority(self):
        self.run_swapped('idl_authority')

if __name__ == '__main__':
    unittest.main()
