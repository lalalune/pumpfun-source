"""Pump v3, creator-setter and create-control differentials must not publish over an input.

Each runner reads the captured Pump image, the shared Mayhem/Pump Fees images,
the captured config snapshot, the signed v3 curve transaction and the
dependency ELFs, then wrote ``--output`` directly. An ``--output`` naming one
of those destroyed captured evidence, or replaced the runner that was
executing.
"""
import gzip
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = (
    "pump_create_control_differential",
    "pump_set_creator_differential",
    "pump_v3_configured_fee_differential",
    "pump_v3_token_extensions_differential",
)
V3 = ("pump_v3_configured_fee_differential", "pump_v3_token_extensions_differential")
IMAGES = (
    "evidence/original/pump/deployed.so",
    "evidence/original/pump_fees/deployed.so",
    "evidence/original/mayhem/deployed.so",
)
CAPTURES = (
    "evidence/original/pump/capture.json",
    "evidence/original/pump_fees/capture.json",
)
METADATA = (
    "evidence/upstream/pump.json",
    "evidence/upstream/pump_fees.json",
)
SNAPSHOT = "research/imported-lab/analysis/pump_fun/config-snapshot.json"
V3_TRANSACTION = "research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json"
EXECUTED_DEPENDENCIES = ("spl_token", "spl_token_2022", "associated_token")
DEPENDENCIES = (*EXECUTED_DEPENDENCIES, "token_metadata")
ALIAS = "report output aliases an input"


class PumpV3ReportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        shutil.copytree(ROOT / "scripts", cls.root / "scripts")
        for relative in (*IMAGES, *CAPTURES, *METADATA, SNAPSHOT, V3_TRANSACTION):
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        for name in DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/deployed.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/deployed.so", target)
        for name in EXECUTED_DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/capture.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/capture.json", target)
        cls.candidate = cls.root / "candidate.so"
        shutil.copyfile(ROOT / IMAGES[0], cls.candidate)
        cls.pristine = {path: path.read_bytes() for path in cls.watched()}

    @classmethod
    def watched(cls):
        """Every file a refused or destructive run could have replaced."""
        yield cls.candidate
        for relative in (*IMAGES, *CAPTURES, *METADATA, SNAPSHOT, V3_TRANSACTION):
            yield cls.root / relative
        for name in DEPENDENCIES:
            yield cls.root / f"evidence/dependencies/{name}/deployed.so"
        for name in EXECUTED_DEPENDENCIES:
            yield cls.root / f"evidence/dependencies/{name}/capture.json"
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
                self.assert_refused(name, self.root / IMAGES[0])

    def test_receipt_cannot_replace_the_captured_config_snapshot(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / SNAPSHOT)

    def test_receipt_cannot_replace_the_candidate(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.candidate)

    def test_receipt_cannot_replace_the_saved_v3_transaction(self):
        for name in V3:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / V3_TRANSACTION)

    def test_receipt_cannot_replace_the_executing_script(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / "scripts" / f"{name}.py")

    def test_fresh_nested_output_publishes_the_report(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                output = self.root / "reports" / name / f"{name}.json"
                completed = self.run_runner(name, output)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                payload = output.read_bytes()
                report = json.loads(gzip.decompress(payload) if payload[:2] == b"\x1f\x8b" else payload)
                self.assertEqual(report["mismatches"], [])
                self.assertGreater(report.get("case_count", len(report["cases"])), 0)
                self.assertEqual([p.name for p in output.parent.iterdir()], [output.name])


if __name__ == "__main__":
    unittest.main()
