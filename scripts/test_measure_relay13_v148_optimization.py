"""Regression checks for optimized-Python rejection in the relay13 v148 measurement.

Sibling of open #2470, which applied the same guard to
scripts/measure_relay_linux_v148.py and explicitly left this script for a
separate change. scripts/measure_relay13_linux_v148.py expresses every
pinned-input admission check as an assert — frozen source seals, selected
source and candidate hashes, prior Linux measurement seals, official
platform-tools size and digest, cargo profile flags — and under -O (or
PYTHONOPTIMIZE) the checks vanish, so a measurement taken from mismatched
inputs could still be recorded.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "measure_relay13_linux_v148.py"


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


class MeasureRelay13V148OptimizationTests(unittest.TestCase):
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
