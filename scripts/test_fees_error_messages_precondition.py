"""Regression checks for the original-error precondition in the Fees error-message differential."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
ORIGINAL = ROOT / "evidence/original/pump_fees/deployed.so"
MESSAGE = b"No fee tiers providedformatThe offset"
MUTATED_MESSAGE = b"No fee tiers providedformxtThe offset"
HARNESS = """
import pathlib, sys
sys.path.insert(0, sys.argv[1])
import fees_error_messages_differential as differential
differential.ORIGINAL = pathlib.Path(sys.argv[2])
sys.argv = ["fees_error_messages_differential.py", "--candidate", sys.argv[3], "--output", sys.argv[4]]
differential.main()
"""


class FeesErrorMessagePreconditionTests(unittest.TestCase):
    def test_original_without_expected_error_fails_in_normal_and_optimized_modes(self):
        source = ORIGINAL.read_bytes()
        self.assertEqual(source.count(MESSAGE), 1)

        with tempfile.TemporaryDirectory(prefix="fees-error-precondition-") as directory:
            temporary = Path(directory)
            original = temporary / "original.so"
            original.write_bytes(source.replace(MESSAGE, MUTATED_MESSAGE))

            for optimization in ([], ["-O"], ["-OO"]):
                with self.subTest(optimization=optimization):
                    output = temporary / (
                        "report-" + ("normal" if not optimization else optimization[0][1:])
                        + ".json"
                    )
                    completed = subprocess.run(
                        [
                            sys.executable,
                            *optimization,
                            "-c",
                            HARNESS,
                            str(SCRIPTS),
                            str(original),
                            str(original),
                            str(output),
                        ],
                        cwd=ROOT,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                    self.assertNotEqual(completed.returncode, 0, completed.stdout)
                    self.assertIn("original configuration case did not emit error 6003", completed.stderr)
                    self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
