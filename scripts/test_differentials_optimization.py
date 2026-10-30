"""Regression checks for optimized-Python rejection in assert-gated Pump and Mayhem differentials.

These runners express their admission checks as asserts: binding a build comparison
to the candidate and its compiled sources, requiring original and candidate to sign
the same transaction, requiring captured fixtures to match their recorded hashes,
and requiring inputs to be unchanged after the run. Under -O (or PYTHONOPTIMIZE)
all of them vanish; pump_incentive_schedule_differential.py, for example, accepted
a build comparison for a different candidate and published its source hashes.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
NAMES = (
    "pump_incentive_schedule_differential.py",
    "pump_quote_control_fresh_differential.py",
    "pump_minimum_fee_differential.py",
    "pump_creator_migration_differential.py",
    "pump_creator_distribution_differential.py",
    "mayhem_burn_sequence.py",
)


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


class DifferentialOptimizationTests(unittest.TestCase):
    def test_optimized_runs_are_rejected(self):
        for name in NAMES:
            for flags, environment in (
                (["-O"], None),
                (["-OO"], None),
                ([], dict(os.environ, PYTHONOPTIMIZE="1")),
            ):
                with self.subTest(script=name, flags=flags, environment=environment is not None):
                    completed = run([sys.executable, *flags, str(SCRIPTS / name), "--help"], environment)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("Normal Python is required", completed.stderr)
                    self.assertNotIn("usage:", completed.stdout)

    def test_normal_python_still_reaches_the_argument_parser(self):
        for name in NAMES:
            with self.subTest(script=name):
                completed = run([sys.executable, str(SCRIPTS / name), "--help"])
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
