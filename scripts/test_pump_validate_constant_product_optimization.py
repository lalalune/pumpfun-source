#!/usr/bin/env python3
"""Regression checks for optimized-Python rejection in the constant-product validator.

Sibling of merged #2514 (Fees aggregate driver) and of #2568 (volume
validator). scripts/pump_validate_constant_product.py expresses its acceptance
checks as bare asserts: the recovered-arithmetic equality check, the output-count
checks, the 100-successful-comparisons floor, and the final ``assert not
failures`` gate, after the report has already been written. Under -O (or
PYTHONOPTIMIZE) all of them vanish, so mismatched reserve arithmetic still
exits 0.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_validate_constant_product.py"


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


class PumpValidateConstantProductOptimizationTests(unittest.TestCase):
    def test_optimized_flag_is_rejected(self):
        completed = run([sys.executable, "-O", str(SCRIPTS / SCRIPT), "--help"])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed = run([sys.executable, str(SCRIPTS / SCRIPT), "--help"],
                        environment)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_normal_python_still_reaches_the_argument_parser(self):
        completed = run([sys.executable, str(SCRIPTS / SCRIPT), "--help"])
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
