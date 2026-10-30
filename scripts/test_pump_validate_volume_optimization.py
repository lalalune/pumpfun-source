#!/usr/bin/env python3
"""Regression checks for optimized-Python rejection in the volume validator.

Sibling of merged #2514, which adds the same guard to the Fees aggregate
driver, and the companion of the guarded aggregate scripts/pump_validate_all.py
and scripts/pump_validate_parallel.py, which cannot reach this individual
validator: scripts/pump_validate_volume.py expresses its whole acceptance gate
as one bare assert at the end (``assert not report['mismatches']``), after the
report has already been written. Under -O (or PYTHONOPTIMIZE) that gate
vanishes, so a differential with mismatched volume-account cases still exits 0.
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_validate_volume.py"


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


class PumpValidateVolumeOptimizationTests(unittest.TestCase):
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
