"""Regression checks for optimized-Python rejection in the initialize-state differential.

Sibling of #2249, #2261, #2459, #2470, #2477, #2504, #2508, #2514 and #2563.
scripts/mayhem_initialize_state_differential.py validates every executed case's
transaction with a bare assert (:148 in the base revision) and then publishes a
per-case `signature_verified: true` field. Under -O (or PYTHONOPTIMIZE) the
assert vanishes and the field is published unverified.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "mayhem_initialize_state_differential.py"


def run(command, environment=None):
    return subprocess.run(
        command,
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class MayhemInitializeStateOptimizationTests(unittest.TestCase):
    def test_optimized_flag_is_rejected(self):
        completed = run([sys.executable, "-O", str(SCRIPTS / SCRIPT), "--help"])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed = run([sys.executable, str(SCRIPTS / SCRIPT), "--help"], environment)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_normal_python_still_reaches_the_argument_parser(self):
        completed = run([sys.executable, str(SCRIPTS / SCRIPT), "--help"])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
