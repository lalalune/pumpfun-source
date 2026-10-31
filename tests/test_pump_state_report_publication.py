"""Pump state and migration differentials must not publish over an input.

These runners read the captured Pump/AMM images, the captured config snapshot,
the saved migration transaction and the dependency ELFs, then truncated
``--output``. An ``--output`` naming one of those destroyed captured evidence,
or replaced the runner that was executing.
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
    "pump_holder_distribution_differential",
    "pump_idl_authority_differential",
    "pump_incentives_admin_differential",
    "pump_volume_sync_differential",
    "pump_migrate_differential",
    "pump_migrate_v2_differential",
)
MIGRATIONS = ("pump_migrate_differential", "pump_migrate_v2_differential")
IMAGES = (
    "evidence/original/pump/deployed.so",
    "evidence/original/pump_amm/deployed.so",
)
DEPENDENCIES = ("spl_token", "spl_token_2022", "associated_token")
SNAPSHOT = "research/imported-lab/analysis/pump_fun/config-snapshot.json"
SAVED_TRANSACTION = "research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json"
ALIAS = "report output aliases an input"


class PumpStateReportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        shutil.copytree(ROOT / "scripts", cls.root / "scripts")
        for relative in (*IMAGES, SNAPSHOT, SAVED_TRANSACTION, "evidence/upstream/pump.json"):
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        for name in DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/deployed.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/deployed.so", target)
        cls.candidate = cls.root / "candidate.so"
        shutil.copyfile(ROOT / IMAGES[0], cls.candidate)
        cls.pristine = {path: path.read_bytes() for path in cls.watched()}

    @classmethod
    def watched(cls):
        """Every file a refused or destructive run could have replaced."""
        yield cls.candidate
        for relative in (*IMAGES, SNAPSHOT, SAVED_TRANSACTION):
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
                self.assert_refused(name, self.root / IMAGES[0])

    def test_receipt_cannot_replace_the_captured_config_snapshot(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / SNAPSHOT)

    def test_receipt_cannot_replace_the_saved_migration_transaction(self):
        for name in MIGRATIONS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / SAVED_TRANSACTION)

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
