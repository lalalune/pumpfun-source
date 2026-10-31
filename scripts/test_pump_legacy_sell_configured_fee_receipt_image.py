"""The configured-fee receipt must name the candidate image the cases executed.

pump_legacy_sell_differential.run() pins the candidate on first use, but the
configured-fee wrapper hashed the live --candidate path after the last case.
"""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/pump_legacy_sell_configured_fee_differential.py"
ORIGINAL = ROOT / "evidence/original/pump/deployed.so"
OTHER = ROOT / "evidence/original/pump_amm/deployed.so"
# Replace the file once the first candidate case has returned.
DRIVER = r"""
import runpy, shutil, sys
from pathlib import Path
script, candidate, replacement, output = sys.argv[1:]
sys.path.insert(0, str(Path(script).parent))
returned = []
def hook(frame, event, arg):
    if (event == 'return' and frame.f_code.co_name == 'run'
            and frame.f_code.co_filename.endswith('pump_legacy_sell_differential.py')):
        returned.append(1)
        if len(returned) == 2:
            sys.setprofile(None)
            shutil.copyfile(replacement, candidate)
sys.setprofile(hook)
sys.argv = [script, '--candidate', candidate, '--output', output]
try:
    runpy.run_path(script, run_name='__main__')
finally:
    sys.setprofile(None)
    if len(returned) < 2:
        raise RuntimeError('candidate case never completed')
"""


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ConfiguredFeeReceiptImageTests(unittest.TestCase):
    def test_replaced_candidate_cannot_change_the_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.so"
            output = Path(directory) / "report.json"
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
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["case_count"], 28)
            self.assertEqual(report["mismatches"], [])
            self.assertEqual(report["candidate_sha256"], sha(ORIGINAL))


if __name__ == "__main__":
    unittest.main()
