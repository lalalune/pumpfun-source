#!/usr/bin/env python3
"""Ensure the Fees external-codec differential rejects optimized Python."""

import os
import subprocess
import sys
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = SCRIPTS / "fees_external_codec_differential.py"
ERROR = "Normal Python is required"


def run(*arguments, environment=None):
    return subprocess.run(
        [sys.executable, *arguments, str(SCRIPT), "--help"],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class FeesExternalCodecOptimizedModeTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        completed = run("-O")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(ERROR, completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        completed = run(environment=dict(os.environ, PYTHONOPTIMIZE="1"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(ERROR, completed.stderr)

    def test_normal_python_reaches_argument_parser(self):
        completed = run()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("usage:", completed.stdout)


if __name__ == "__main__":
    unittest.main()
