"""The legacy cashback receipt must name the candidate image the cases executed.

pump_legacy_buy_differential.run() pins the candidate on first use, but this
wrapper hashed the live --candidate path after the last case.
"""

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/pump_legacy_cashback_differential.py"
ORIGINAL = ROOT / "evidence/original/pump/deployed.so"
OTHER = ROOT / "evidence/original/pump_amm/deployed.so"
# Replace the file once the first candidate case has returned.
DRIVER = r"""
import runpy, shutil, sys
from pathlib import Path
script, candidate, replacement, output = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
replaced = []
def hook(frame, event, arg):
    if (event == 'return' and frame.f_code.co_name == 'run'
            and frame.f_code.co_filename.endswith('pump_legacy_buy_differential.py')
            and frame.f_locals.get('binary')):
        sys.setprofile(None)
        shutil.copyfile(replacement, candidate)
        replaced.append(1)
sys.setprofile(hook)
sys.argv = [script, '--candidate', candidate, '--output', output]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    sys.setprofile(None)
    if not replaced:
        raise RuntimeError('candidate case never completed')
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class LegacyCashbackReceiptImageTests(unittest.TestCase):
    def test_replaced_candidate_cannot_change_the_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.so"
            output = Path(directory) / "report.json.gz"
            shutil.copyfile(ORIGINAL, candidate)
            completed = subprocess.run(
                [sys.executable, "-B", "-c", DRIVER, str(SCRIPT), str(candidate), str(OTHER), str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=300,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
            self.assertEqual(sha(candidate), sha(OTHER))
            report = json.loads(gzip.decompress(output.read_bytes()))
            self.assertEqual(report["case_count"], 14)
            self.assertEqual(report["mismatches"], [])
            self.assertEqual(report["candidate_sha256"], sha(ORIGINAL))


if __name__ == "__main__":
    unittest.main()
