"""Regression checks for optimized-Python rejection in the Mayhem burn-sequence verifier.

Sibling of open #2249, which adds the same guard to the five Mayhem trade
receipt verifiers but cannot reach this sixth Mayhem receipt verifier:
scripts/verify_mayhem_burn_sequence.py expresses every acceptance check as
an assert, so under -O (or PYTHONOPTIMIZE=1) the checks vanish and garbage
receipts verify with success True.
"""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "verify_mayhem_burn_sequence.py"


def run_optimized(args):
    return subprocess.run(
        [sys.executable, "-O", str(SCRIPTS / SCRIPT), *args],
        cwd=SCRIPTS.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class BurnSequenceOptimizationTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        completed = run_optimized(["--help"])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_optimized_python_cannot_verify_garbage_receipts(self):
        with tempfile.TemporaryDirectory(prefix="burn-sequence-opt-") as temporary:
            root = Path(temporary)
            fixtures = root / "fixtures"
            receipts = root / "receipts"
            fixtures.mkdir()
            receipts.mkdir()
            (fixtures / "fixture-manifest.json").write_text(json.dumps({
                "snapshots": {"eligible": {"accounts": {}}},
                "eligible_families": [],
            }))
            (receipts / "comparison.json").write_text(json.dumps({
                "case_count": 999,
                "signed_transactions": 999,
                "inputs_unchanged": False,
                "mismatches": ["bogus"],
                "input_sha256": {},
                "runner_sha256": "deadbeef",
                "cases": [{"original": {"sequential_second": True, "binary_sha256": "x"},
                           "candidate": {"binary_sha256": "y"}}],
            }))
            completed = run_optimized(["--fixtures", str(fixtures), "--receipts", str(receipts)])
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Normal Python is required", completed.stderr)
            self.assertFalse((receipts / "verification.json").exists())


if __name__ == "__main__":
    unittest.main()
