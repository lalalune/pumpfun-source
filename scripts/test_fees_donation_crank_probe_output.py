"""The crank probe must not publish its report over a file it reads.

scripts/fees_donation_crank_probe.py wrote --output directly once every case
had run. Its siblings admit the path first through PumpReport.
"""

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fees_donation_crank_probe.py"
ORIGINAL = ROOT / "evidence/original/pump_fees/deployed.so"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*arguments):
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class CrankProbeOutputTests(unittest.TestCase):
    def test_output_cannot_replace_the_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.so"
            shutil.copyfile(ORIGINAL, candidate)
            completed = run("--candidate", candidate, "--output", candidate)
            self.assertEqual(sha(candidate), sha(ORIGINAL), completed.stdout[-500:])
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("aliases an input", completed.stderr)

    def test_hard_linked_output_cannot_replace_the_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.so"
            output = Path(directory) / "report.json"
            shutil.copyfile(ORIGINAL, candidate)
            output.hardlink_to(candidate)
            completed = run("--candidate", candidate, "--output", output)
            self.assertEqual(sha(candidate), sha(ORIGINAL), completed.stdout[-500:])
            self.assertNotEqual(completed.returncode, 0)

    def test_fresh_output_still_receives_the_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested/report.json"
            completed = run("--candidate", ORIGINAL, "--output", output)
            self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
            self.assertIn('"mismatches": []', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
