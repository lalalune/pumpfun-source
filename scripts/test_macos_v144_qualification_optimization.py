"""Regression checks for optimized-Python rejection in the v144 qualification.

Sibling of #2249 and #2793. pump_macos_frontier_qualification.py already opens
with the refusal; scripts/pump_macos_v144_qualification.py expresses every
integrity gate — host, archive and SDK digests, determinism, thresholds — as
bare asserts and writes measurement.json and MANIFEST.json regardless, so under
-O (or PYTHONOPTIMIZE) a tampered or regressed run still publishes a passing
qualification.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_macos_v144_qualification.py"


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


class MacosV144QualificationOptimizationTests(unittest.TestCase):
    def test_optimized_flag_is_rejected(self):
        completed = run([sys.executable, "-O", str(SCRIPTS / SCRIPT), "--help"])
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed = run([sys.executable, str(SCRIPTS / SCRIPT), "--help"], environment)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
