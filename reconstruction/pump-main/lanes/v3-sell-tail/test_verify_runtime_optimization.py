"""Regression check for optimized-Python rejection in the v3-sell-tail receipt verifier."""

from pathlib import Path
import subprocess
import sys
import unittest


class VerifyRuntimeOptimizationTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        script = Path(__file__).resolve().parent / "verify_runtime.py"
        for flags in (["-O"], ["-OO"]):
            with self.subTest(flags=flags):
                completed = subprocess.run(
                    [sys.executable, *flags, str(script)],
                    cwd=script.parent,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("Normal Python is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
