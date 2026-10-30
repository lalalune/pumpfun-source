"""Regression checks for optimized-Python rejection in the macOS frontier replay.

Sibling of #2249, #2261, #2459, #2470, #2477 and #2504. scripts/pump_replay_macos_frontier.py
publishes qualification.json with literal 'status': 'passed' claims whose provenance
bindings are enforced only by bare asserts — the native input-manifest digests (:66),
the build record and candidate/source SHA binding (:76-79) and the sub-report SHA
chain with exact suite and case counts (:115-126). Under -O (or PYTHONOPTIMIZE)
those checks vanish and drifted inputs can still produce a published 'passed'
artifact. The script has no argument parser, so the refusal is observed on any
invocation.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_replay_macos_frontier.py"


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


class ReplayMacosFrontierOptimizationTests(unittest.TestCase):
    def test_optimized_flag_is_rejected(self):
        completed = run([sys.executable, "-O", str(SCRIPTS / SCRIPT)])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed = run([sys.executable, str(SCRIPTS / SCRIPT)], environment)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
