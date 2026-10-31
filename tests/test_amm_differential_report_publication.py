"""AMM differential runners must not publish their receipt over an input.

Each runner reads the captured pump_amm image, the captured dependency ELFs,
the captured trade/migration fixtures and the AMM source tree, then truncated
``--output``. An ``--output`` naming one of those made the run destroy evidence
a later report depends on, or replace the script that was executing.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = {
    "pump_amm_boost_burn_differential": (),
    "pump_amm_cashback_differential": (),
    "pump_amm_create_differential": (),
    "pump_amm_creator_reassignment_cto_differential": (),
    "pump_amm_creator_reassignment_differential": (),
    "pump_amm_incentives_differential": ("--family", "sync"),
    "pump_amm_migration_create_differential": (),
    "pump_amm_transfer_creator_differential": (),
}
FIXTURES = (
    "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json",
    "research/imported-lab/analysis/pump_fun/config-snapshot.json",
)
IMAGES = {
    "evidence/original/pump/deployed.so": "pump",
    "evidence/original/pump_amm/deployed.so": "pump_amm",
    "evidence/original/pump_fees/deployed.so": "pump_fees",
    "evidence/original/mayhem/deployed.so": "mayhem",
}
UPSTREAM = ("pump", "pump_amm", "pump_fees")
DEPENDENCIES = ("spl_token", "spl_token_2022", "associated_token")
ALIAS = "report output aliases an input"


class AMMReportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        shutil.copytree(ROOT / "scripts", cls.root / "scripts")
        shutil.copytree(ROOT / "programs" / "pump-amm", cls.root / "programs" / "pump-amm")
        shutil.copytree(ROOT / "research/imported-lab/analysis/pump_fun",
                        cls.root / "research/imported-lab/analysis/pump_fun")
        for relative in IMAGES:
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        for name in UPSTREAM:
            target = cls.root / f"evidence/upstream/{name}.json"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/upstream/{name}.json", target)
        for name in DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/deployed.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/deployed.so", target)
        cls.candidate = cls.root / "candidate.so"
        shutil.copyfile(ROOT / "evidence/original/pump_amm/deployed.so", cls.candidate)
        cls.pristine = {path: path.read_bytes() for path in cls.watched()}

    @classmethod
    def watched(cls):
        """Every file a refused or destructive run could have replaced."""
        yield cls.candidate
        for relative in (*IMAGES, *FIXTURES):
            yield cls.root / relative
        for name in UPSTREAM:
            yield cls.root / f"evidence/upstream/{name}.json"
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
             "--candidate", str(self.candidate), "--output", str(output), *RUNNERS[name]],
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
                self.assert_refused(name, self.root / "evidence/original/pump_amm/deployed.so")

    def test_receipt_cannot_replace_the_candidate(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.candidate)

    def test_receipt_cannot_replace_a_captured_fixture(self):
        for name in RUNNERS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / FIXTURES[0])

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
                report = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(report["mismatches"], [])
                self.assertGreater(report["case_count"], 0)
                self.assertEqual([p.name for p in output.parent.iterdir()], [output.name])


if __name__ == "__main__":
    unittest.main()
