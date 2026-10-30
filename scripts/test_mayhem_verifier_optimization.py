"""Regression checks for optimized-Python rejection in Mayhem receipt verifiers."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPTS = (
    "verify_mayhem_buy.py",
    "verify_mayhem_buy_v2.py",
    "verify_mayhem_pump_swap.py",
    "verify_mayhem_sell.py",
    "verify_mayhem_sell_v2.py",
)


class MayhemVerifierOptimizationTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        scripts = Path(__file__).resolve().parent
        for name in SCRIPTS:
            with self.subTest(script=name):
                completed = subprocess.run(
                    [sys.executable, "-O", str(scripts / name), "--help"],
                    cwd=scripts.parent,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("Normal Python is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
