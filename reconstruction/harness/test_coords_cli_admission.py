"""coords.py CLI lookups fail closed with diagnostics, not tracebacks."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[1]
ORIGINAL = REPO / "evidence/original/pump/deployed.so"


def run_coords(arguments):
    return subprocess.run(
        [sys.executable, "-B", str(HARNESS / "coords.py"), *arguments],
        cwd=REPO, capture_output=True, text=True, timeout=20,
    )


class CoordsCliAdmissionTests(unittest.TestCase):
    def test_unknown_window_start_is_a_diagnostic_exit(self):
        result = run_coords(["window", "0x1"])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("is not an original window start", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unknown_function_address_is_a_diagnostic_exit(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate.so"
            shutil.copyfile(ORIGINAL, candidate)
            result = run_coords(["fn", "0x1", "--cand", str(candidate)])
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("is not a function symbol", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_nonnumeric_window_start_is_an_argparse_error(self):
        result = run_coords(["window", "not-an-address"])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("is not a numeric address", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_nonnumeric_function_address_is_an_argparse_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate.so"
            shutil.copyfile(ORIGINAL, candidate)
            result = run_coords(["fn", "not-an-address", "--cand", str(candidate)])
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
