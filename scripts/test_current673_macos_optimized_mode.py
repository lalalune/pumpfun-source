#!/usr/bin/env python3
"""Ensure current673 macOS controllers reject optimized Python at entry."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
CONTROLLERS = (
    "pump_current673_macos_control.py",
    "pump_current673_macos_candidate.py",
)
ERROR = "Normal Python is required"


def run(script, *arguments, environment=None):
    return subprocess.run(
        [sys.executable, *arguments, str(SCRIPTS / script), "--help"],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class Current673MacosOptimizedModeTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        for script in CONTROLLERS:
            with self.subTest(script=script):
                completed = run(script, "-O")
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(ERROR, completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        for script in CONTROLLERS:
            with self.subTest(script=script):
                completed = run(script, environment=environment)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn(ERROR, completed.stderr)

    def test_normal_python_reaches_argument_parser(self):
        for script in CONTROLLERS:
            with self.subTest(script=script):
                completed = run(script)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
