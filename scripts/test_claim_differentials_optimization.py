"""Regression checks for optimized-Python rejection in the Pump claim differentials.

scripts/pump_claim_boundary_differential.py and scripts/pump_claim_panic_differential.py
express their admission checks as asserts: refusing to overwrite retained results,
binding the build comparison to the candidate, requiring the original to emit the
expected panic message, and requiring inputs to be unchanged after the run. Under
-O (or PYTHONOPTIMIZE) all of them vanish, so an optimized run overwrote a retained
report and could publish results for a mismatched build or changed inputs.
"""

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ORIGINAL = ROOT / "evidence/original/pump/deployed.so"
NAMES = ("pump_claim_boundary_differential.py", "pump_claim_panic_differential.py")


def run(command, environment=None):
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class ClaimDifferentialOptimizationTests(unittest.TestCase):
    def test_optimized_runs_are_rejected_and_keep_retained_output(self):
        with tempfile.TemporaryDirectory(prefix="claim-optimization-") as directory:
            retained = Path(directory) / "retained.json.gz"
            for name in NAMES:
                for flags, environment in (
                    (["-O"], None),
                    (["-OO"], None),
                    ([], dict(os.environ, PYTHONOPTIMIZE="1")),
                ):
                    with self.subTest(script=name, flags=flags, environment=environment is not None):
                        retained.write_bytes(b"retained")
                        completed = run(
                            [sys.executable, *flags, str(SCRIPTS / name),
                             "--candidate", str(ORIGINAL), "--output", str(retained)],
                            environment,
                        )
                        self.assertNotEqual(completed.returncode, 0)
                        self.assertIn("Normal Python is required", completed.stderr)
                        self.assertEqual(retained.read_bytes(), b"retained")

    def test_normal_python_still_reaches_the_argument_parser(self):
        for name in NAMES:
            with self.subTest(script=name):
                completed = run([sys.executable, str(SCRIPTS / name), "--help"])
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
