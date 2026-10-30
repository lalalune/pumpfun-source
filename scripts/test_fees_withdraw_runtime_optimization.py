"""Regression checks for optimized-Python rejection in the Fees withdraw runtime extractor.

Sibling of #2249, #2261, #2459 and #2470. scripts/prepare_fees_withdraw_runtime.py
expresses every admission check as an assert — the focused-checkpoint allowlist and
manifest seal, and, inside the extraction loop, archive member path-traversal,
symlink and hardlink rejections. Under -O (or PYTHONOPTIMIZE) all of them vanish,
so an optimized run would extract an unsealed harness and follow traversal or link
members while still reporting status PASS.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "prepare_fees_withdraw_runtime.py"


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


class FeesWithdrawRuntimeOptimizationTests(unittest.TestCase):
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
