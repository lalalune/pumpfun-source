#!/usr/bin/env python3
"""The exact-body inventory must not publish under optimized Python.

Its admission gate is plain assert statements: the captured image hash, the
1,035-window count and contiguous coverage of .text. Under -O or PYTHONOPTIMIZE
those checks vanish, so a truncated inventory published a successful report.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
TOOL = "pump_exact_body_inventory.py"
HELPER = "pump_quote_control_function_match.py"
WINDOWS = Path("reconstruction/base/functions.tsv")


@unittest.skipUnless(shutil.which("true"), "requires a no-output symbol reader")
class ExactBodyInventoryOptimizationTests(unittest.TestCase):
    def run_truncated(self, *interpreter, environment=None):
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary)
            (checkout / "scripts").mkdir()
            for name in (TOOL, HELPER):
                shutil.copy(SCRIPTS / name, checkout / "scripts" / name)
            os.symlink(ROOT / "evidence", checkout / "evidence")
            inventory = checkout / WINDOWS
            inventory.parent.mkdir(parents=True)
            lines = (ROOT / WINDOWS).read_text(encoding="utf-8").splitlines(True)
            header, first = lines[0], next(
                line for line in lines[1:]
                if line.startswith("pump\t") and "\tselected\t" in line)
            inventory.write_text(header + first, encoding="utf-8")
            report = checkout / "report.json"
            completed = subprocess.run(
                [*interpreter, str(checkout / "scripts" / TOOL),
                 "--candidate", str(ROOT / "evidence/original/pump/deployed.so"),
                 "--output", str(report), "--objdump", "true"],
                env=environment,
                capture_output=True,
                text=True,
            )
            return completed, report.exists()

    def test_optimized_flag_does_not_publish_a_truncated_inventory(self):
        completed, published = self.run_truncated(sys.executable, "-B", "-O")
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("Normal Python is required", completed.stderr)
        self.assertFalse(published)

    def test_pythonoptimize_does_not_publish_a_truncated_inventory(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        completed, published = self.run_truncated(
            sys.executable, "-B", environment=environment)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("Normal Python is required", completed.stderr)
        self.assertFalse(published)

    def test_normal_python_still_rejects_the_truncated_inventory(self):
        completed, published = self.run_truncated(sys.executable, "-B")
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("AssertionError", completed.stderr)
        self.assertFalse(published)


if __name__ == "__main__":
    unittest.main()
