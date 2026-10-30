"""Path-boundary regressions for the captured-loader receipt writer."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
WRAPPER = HERE / "pump_with_captured_loader.py"


class CapturedLoaderReceiptPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="captured-loader-paths-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scripts = self.root / "scripts"
        self.scripts.mkdir()
        self.wrapper = self.scripts / WRAPPER.name
        shutil.copyfile(WRAPPER, self.wrapper)
        (self.scripts / "pump_captured_loader.py").write_text(
            "from pathlib import Path\n"
            "ROOT = Path(__file__).resolve().parents[1]\n"
            "LOADS = []\n"
            "def install():\n"
            "    pass\n",
            encoding="utf-8",
        )
        evidence = self.root / "evidence/original/pump"
        evidence.mkdir(parents=True)
        (evidence / "capture.json").write_text(
            json.dumps({"program": "program", "programdata": "programdata"}) + "\n",
            encoding="utf-8",
        )
        (evidence / "program-account.bin").write_bytes(b"program-account")
        (evidence / "programdata-account.bin").write_bytes(b"programdata-account")
        self.harness = self.root / "harness.py"
        self.harness.write_text("print('fixture completed')\n", encoding="utf-8")

    def run_wrapper(self, receipt):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.wrapper),
                "--receipt",
                str(receipt),
                str(self.harness),
            ],
            text=True,
            capture_output=True,
        )

    def test_receipt_cannot_replace_harness(self):
        before = self.harness.read_bytes()
        result = self.run_wrapper(self.harness)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt path aliases protected input", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.harness.read_bytes(), before)

    def test_receipt_cannot_replace_capture(self):
        capture = self.root / "evidence/original/pump/capture.json"
        before = capture.read_bytes()
        result = self.run_wrapper(capture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt path aliases protected input", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(capture.read_bytes(), before)

    def test_receipt_symlink_cannot_replace_bound_input(self):
        account = self.root / "evidence/original/pump/program-account.bin"
        before = account.read_bytes()
        receipt = self.root / "receipt.json"
        receipt.symlink_to(account)
        result = self.run_wrapper(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt path aliases protected input", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(account.read_bytes(), before)

    def test_receipt_hardlink_cannot_replace_bound_input(self):
        account = self.root / "evidence/original/pump/program-account.bin"
        before = account.read_bytes()
        receipt = self.root / "receipt.json"
        receipt.hardlink_to(account)
        result = self.run_wrapper(receipt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("receipt path aliases protected input", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(account.read_bytes(), before)

    def test_distinct_receipt_is_written(self):
        receipt = self.root / "work/receipt.json"
        result = self.run_wrapper(receipt)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(receipt.read_text())
        self.assertEqual(record["harness"], str(self.harness.resolve()))
        self.assertEqual(record["loads"], [])
        expected = hashlib.sha256(self.harness.read_bytes()).hexdigest()
        self.assertEqual(record["input_sha256"][str(self.harness.resolve())], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
