"""Regression checks for optimized-Python rejection in the token-dependency builder.

Sibling of open #2436, which applied the same guard to
scripts/pump_build_verified.py, and of open #2419, which applied it to
scripts/pump_verify_dependencies.py. scripts/pump_build_token_dependency.py
expresses every pinned-build admission check as an assert — the source
commit, a fresh and clean checkout, no pre-existing build target, the
recorded baseline and patched source hashes, source unchanged after the
build, a candidate output, and a verified-zero trailing allocation suffix —
and under -O (or PYTHONOPTIMIZE) the checks vanish, so a build from a
mismatched or dirty source tree could still be recorded as verified.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_build_token_dependency.py"


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


class BuildTokenDependencyOptimizationTests(unittest.TestCase):
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
