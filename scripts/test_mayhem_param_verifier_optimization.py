"""Regression checks for optimized-Python rejection in Mayhem set-params receipt verifiers."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPTS = (
    "verify_pump_set_mayhem_params_synthetic.py",
    "verify_pump_set_mayhem_params_8099.py",
)


class MayhemParamVerifierOptimizationTests(unittest.TestCase):
    def test_optimized_python_is_rejected(self):
        scripts = Path(__file__).resolve().parent
        for name in SCRIPTS:
            for flags in (["-O"], ["-OO"]):
                with self.subTest(script=name, flags=flags):
                    completed = subprocess.run(
                        [sys.executable, *flags, str(scripts / name), "--help"],
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
