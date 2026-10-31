"""Pump create/extend differentials must not publish a receipt over an input.

These runners read the captured Pump and Mayhem images, the captured config
snapshot and the dependency ELFs, then truncated ``--output``. An ``--output``
naming one of those destroyed captured evidence, or replaced the runner that was
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
MODULES = (
    "pump_create_quote_differential.py",
    "pump_create_v2_differential.py",
    "pump_create_mayhem_differential.py",
    "pump_extend_differential.py",
    "pump_amm_reusable_harness.py",
    "pump_differential_output.py",
)
IMAGES = (
    "evidence/original/pump/deployed.so",
    "evidence/original/mayhem/deployed.so",
)
DEPENDENCIES = ("spl_token", "spl_token_2022", "associated_token", "token_metadata")
SNAPSHOT = "research/imported-lab/analysis/pump_fun/config-snapshot.json"
MAYHEM_INPUTS = (
    "pump_create_quote_differential",
    "pump_create_v2_differential",
    "pump_create_mayhem_differential",
)
ALIAS = "report output aliases an input"


class PumpCreateExtendReportPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        (cls.root / "scripts").mkdir()
        for name in MODULES:
            shutil.copyfile(ROOT / "scripts" / name, cls.root / "scripts" / name)
        for relative in (*IMAGES, SNAPSHOT, "evidence/upstream/pump.json"):
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        for name in DEPENDENCIES:
            target = cls.root / f"evidence/dependencies/{name}/deployed.so"
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / f"evidence/dependencies/{name}/deployed.so", target)
        cls.pump = cls.root / "candidate-pump.so"
        cls.mayhem = cls.root / "candidate-mayhem.so"
        shutil.copyfile(ROOT / IMAGES[0], cls.pump)
        shutil.copyfile(ROOT / IMAGES[1], cls.mayhem)
        cls.pristine = {path: path.read_bytes() for path in cls.watched()}

    @classmethod
    def watched(cls):
        """Every file a refused or destructive run could have replaced."""
        yield cls.pump
        yield cls.mayhem
        for relative in (*IMAGES, SNAPSHOT):
            yield cls.root / relative
        for name in DEPENDENCIES:
            yield cls.root / f"evidence/dependencies/{name}/deployed.so"
        for name in MODULES[:4]:
            yield cls.root / "scripts" / name

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def tearDown(self):
        # A run that overwrote an input would otherwise poison later subtests.
        for path, original in self.pristine.items():
            if path.read_bytes() != original:
                path.write_bytes(original)

    def run_runner(self, name, output):
        command = [sys.executable, "-B", str(self.root / "scripts" / f"{name}.py")]
        if name == "pump_create_mayhem_differential":
            command += ["--candidate-pump", str(self.pump), "--candidate-mayhem", str(self.mayhem)]
        else:
            command += ["--candidate", str(self.pump)]
        return subprocess.run([*command, "--output", str(output)], cwd=self.root,
                              capture_output=True, text=True)

    def assert_refused(self, name, target):
        original = target.read_bytes()
        completed = self.run_runner(name, target)
        self.assertNotEqual(completed.returncode, 0, completed.stdout)
        self.assertIn(ALIAS, completed.stderr)
        self.assertEqual(target.read_bytes(), original)

    def test_receipt_cannot_replace_the_captured_pump_image(self):
        for name in MAYHEM_INPUTS + ("pump_extend_differential",):
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / IMAGES[0])

    def test_receipt_cannot_replace_the_captured_mayhem_image(self):
        for name in MAYHEM_INPUTS:
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / IMAGES[1])

    def test_receipt_cannot_replace_the_captured_config_snapshot(self):
        for name in MAYHEM_INPUTS + ("pump_extend_differential",):
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / SNAPSHOT)

    def test_receipt_cannot_replace_the_executing_script(self):
        for name in MAYHEM_INPUTS + ("pump_extend_differential",):
            with self.subTest(runner=name):
                self.assert_refused(name, self.root / "scripts" / f"{name}.py")

    def test_fresh_nested_output_publishes_the_report(self):
        for name in MAYHEM_INPUTS + ("pump_extend_differential",):
            with self.subTest(runner=name):
                output = self.root / "reports" / name / f"{name}.json.gz"
                completed = self.run_runner(name, output)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(gzip.decompress(output.read_bytes()))
                self.assertEqual(report["mismatches"], [])
                self.assertGreater(len(report["cases"]), 0)
                self.assertEqual([p.name for p in output.parent.iterdir()], [output.name])


if __name__ == "__main__":
    unittest.main()
