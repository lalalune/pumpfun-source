"""Regression checks for mismatch exits in the Fees error-message differential."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).with_name("fees_error_messages_differential.py")
ORIGINAL = ROOT / "evidence/original/pump_fees/deployed.so"
MESSAGE = b"No fee tiers providedformatThe offset"
MUTATED_MESSAGE = b"No fee tiers providedformxtThe offset"


class FeesErrorMessageExitTests(unittest.TestCase):
    def test_real_message_mismatch_fails_in_normal_and_optimized_modes(self):
        source = ORIGINAL.read_bytes()
        self.assertEqual(source.count(MESSAGE), 1)

        with tempfile.TemporaryDirectory(prefix="fees-error-exit-") as directory:
            temporary = Path(directory)
            candidate = temporary / "candidate.so"
            candidate.write_bytes(source.replace(MESSAGE, MUTATED_MESSAGE))

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
                            str(SCRIPT),
                            "--candidate",
                            str(candidate),
                            "--output",
                            str(output),
                        ],
                        cwd=ROOT,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 1, completed.stderr)
                    self.assertIn("update_fee_config-count-51", completed.stdout)
                    self.assertIn("update_fee_shares-new-count-11", completed.stdout)
                    self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
