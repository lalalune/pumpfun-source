"""Regression checks for optimized-Python rejection in the Fees aggregate driver.

Sibling of #2249, #2261, #2459, #2470, #2477, #2504 and #2508, and the aggregate
companion of #2474 (which guarded the individual suites). scripts/fees_validate_all.py
binds every suite report's original/candidate SHA-256 to the aggregate report only
through a bare assert at :17, and its final no-mismatches gate is an assert at :18.
Under -O (or PYTHONOPTIMIZE, which also propagates to the spawned suites) those
checks vanish, so an aggregate can mix suites run against different ELF inputs and
still exit 0.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "fees_validate_all.py"


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


class FeesValidateAllOptimizationTests(unittest.TestCase):
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
