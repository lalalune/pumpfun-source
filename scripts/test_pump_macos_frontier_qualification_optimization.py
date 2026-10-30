#!/usr/bin/env python3
"""Regression checks for optimized-Python rejection in the macOS frontier qualification.

scripts/pump_macos_frontier_qualification.py enforces its native tool and target
library digests, the primary archive digest, repeat-build byte equality, the
original capture digest and the exact normalized-match counts only with bare
asserts. Under -O (or PYTHONOPTIMIZE) those checks vanish and the script still
writes measurement.json and MANIFEST.json. The script has no argument parser and
starts building on any normal invocation, so the normal-Python check imports it.
"""

from pathlib import Path
import os
import subprocess
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_macos_frontier_qualification.py"


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


class MacosFrontierQualificationOptimizationTests(unittest.TestCase):
    def test_optimized_flag_is_rejected(self):
        for flag in ("-O", "-OO"):
            with self.subTest(flag=flag):
                completed = run([sys.executable, flag, str(SCRIPTS / SCRIPT)])
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("Normal Python is required", completed.stderr)

    def test_pythonoptimize_environment_is_rejected(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed = run([sys.executable, str(SCRIPTS / SCRIPT)], environment)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("Normal Python is required", completed.stderr)

    def test_normal_python_still_imports_the_module(self):
        environment = {key: value for key, value in os.environ.items() if key != "PYTHONOPTIMIZE"}
        completed = run([sys.executable, "-B", "-c",
                         "import sys; sys.path.insert(0, 'scripts'); "
                         "import pump_macos_frontier_qualification as m; print(callable(m.main))"],
                        environment)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "True")


if __name__ == "__main__":
    unittest.main()
