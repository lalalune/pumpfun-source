"""Fees probe receipts must not publish over an input.

The donation crank probe and the recovered fee-handler validator read the
captured Pump Fees image, the donation relay and SPL dependency ELFs, the
shared AMM fixture and the saved fee-selector receipts, then wrote
``--output`` directly. An ``--output`` naming one of those destroyed captured
evidence, or replaced the runner that was executing.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = (
    "fees_donation_crank_probe",
    "validate_fee_handlers",
)
IMAGE = "evidence/original/pump_fees/deployed.so"
DEPENDENCIES = ("spl_token", "spl_token_2022", "associated_token", "donation_relay")
AMM_FIXTURE = "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json"
SELECTOR_RECEIPTS = (
    "research/fees-query-inputs/quote-selector-cases.json.gz",
    "research/fees-query-inputs/fee-selector-cases.json.gz",
)
ALIAS = "report output aliases an input"


class FeesProbeReportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        shutil.copytree(ROOT / "scripts", cls.root / "scripts")
        for relative in (IMAGE, "evidence/upstream/pump_fees.json", AMM_FIXTURE, *SELECTOR_RECEIPTS):
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        for name in DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/deployed.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/deployed.so", target)
        cls.candidate = cls.root / "candidate.so"
        shutil.copyfile(ROOT / IMAGE, cls.candidate)
        cls.pristine = {path: path.read_bytes() for path in cls.watched()}

    @classmethod
    def watched(cls):
        """Every file a refused or destructive run could have replaced."""
        yield cls.candidate
        for relative in (IMAGE, "evidence/upstream/pump_fees.json", AMM_FIXTURE, *SELECTOR_RECEIPTS):
            yield cls.root / relative
        for name in DEPENDENCIES:
            yield cls.root / f"evidence/dependencies/{name}/deployed.so"
        for name in RUNNERS:
            yield cls.root / "scripts" / f"{name}.py"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def tearDown(self):
        # A run that overwrote an input would otherwise poison later subtests.
        for path, original in self.pristine.items():
            if path.read_bytes() != original:
                path.write_bytes(original)

    def run_runner(self, name, output):
        return subprocess.run(
            [sys.executable, "-B", str(self.root / "scripts" / f"{name}.py"),
             "--candidate", str(self.candidate), "--output", str(output)],
            cwd=self.root, capture_output=True, text=True)

    def assert_refused(self, name, target):
        original = target.read_bytes()
        completed = self.run_runner(name, target)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn(ALIAS, completed.stderr)
        self.assertEqual(target.read_bytes(), original)

    def test_receipt_cannot_replace_the_captured_image(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / IMAGE)

    def test_receipt_cannot_replace_the_candidate(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.candidate)

    def test_receipt_cannot_replace_the_executing_script(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / "scripts" / f"{name}.py")

    def test_receipt_cannot_replace_the_shared_amm_fixture(self):
        self.assert_refused("fees_donation_crank_probe", self.root / AMM_FIXTURE)

    def test_receipt_cannot_replace_the_saved_selector_receipts(self):
        for relative in SELECTOR_RECEIPTS:
            with self.subTest(receipt=relative):
                self.assert_refused("validate_fee_handlers", self.root / relative)

    def test_fresh_nested_output_publishes_the_report(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                output = self.root / "reports" / name / f"{name}.json"
                completed = self.run_runner(name, output)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(output.read_bytes())
                self.assertEqual(report.get("mismatches", report.get("failures")), [])
                self.assertGreater(report.get("case_count", len(report["cases"])), 0)
                self.assertEqual([p.name for p in output.parent.iterdir()], [output.name])


if __name__ == "__main__":
    unittest.main()
