"""Mayhem validators must not publish their receipt over one of their inputs.

The six validators read the captured Mayhem image, the captured dependency
ELFs and the program sources they hash into the report, then truncate
``--output``. Passing an input as ``--output`` therefore destroyed evidence a
later report depends on, or replaced the very script that was executing.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = (
    "mayhem_validate_admin",
    "mayhem_validate_extend",
    "mayhem_validate_fee_recipient",
    "mayhem_validate_quote_withdraw",
    "mayhem_validate_sweeps",
    "mayhem_validate_withdraw",
)
MODULES = tuple(f"{name}.py" for name in VALIDATORS) + ("pump_differential_output.py",)
READ_INPUTS = (
    "evidence/original/mayhem/deployed.so",
    "evidence/dependencies/spl_token/deployed.so",
    "evidence/dependencies/spl_token_2022/deployed.so",
    "evidence/dependencies/associated_token/deployed.so",
    "programs/mayhem/Cargo.toml",
    "programs/mayhem/Cargo.lock",
    "programs/mayhem/src/lib.rs",
)
ALIAS = "report output aliases an input"


class MayhemValidateReportPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "scripts").mkdir()
        for name in MODULES:
            shutil.copyfile(ROOT / "scripts" / name, self.root / "scripts" / name)
        for relative in READ_INPUTS:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.candidate = self.root / "candidate.so"
        shutil.copyfile(ROOT / "evidence/original/mayhem/deployed.so", self.candidate)

    def tearDown(self):
        self.temporary.cleanup()

    def run_validator(self, name, output):
        return subprocess.run(
            [sys.executable, "-B", str(self.root / "scripts" / f"{name}.py"),
             "--candidate", str(self.candidate), "--output", str(output)],
            capture_output=True, text=True)

    def assert_refused(self, name, target):
        """The validator exits without touching the aliased input."""
        original = target.read_bytes()
        completed = self.run_validator(name, target)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn(ALIAS, completed.stderr)
        self.assertEqual(target.read_bytes(), original)

    def test_receipt_cannot_replace_the_captured_image(self):
        for name in VALIDATORS:
            with self.subTest(validator=name):
                self.assert_refused(name, self.root / READ_INPUTS[0])

    def test_receipt_cannot_replace_the_candidate(self):
        for name in VALIDATORS:
            with self.subTest(validator=name):
                self.assert_refused(name, self.candidate)

    def test_receipt_cannot_replace_a_hashed_program_source(self):
        for name in VALIDATORS:
            with self.subTest(validator=name):
                self.assert_refused(name, self.root / "programs/mayhem/src/lib.rs")

    def test_receipt_cannot_replace_the_executing_script(self):
        for name in VALIDATORS:
            with self.subTest(validator=name):
                self.assert_refused(name, self.root / "scripts" / f"{name}.py")

    def test_fresh_nested_output_publishes_the_report(self):
        for name in VALIDATORS:
            with self.subTest(validator=name):
                output = self.root / "reports" / name / f"{name}.json"
                completed = self.run_validator(name, output)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(report["mismatches"], [])
                self.assertGreater(report["case_count"], 0)
                self.assertEqual([p.name for p in output.parent.iterdir()], [output.name])


if __name__ == "__main__":
    unittest.main()
