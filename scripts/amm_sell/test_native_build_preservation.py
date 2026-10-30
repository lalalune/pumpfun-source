"""Offline checks that failed native rebuilds preserve the prior published output."""
from pathlib import Path
import importlib.util
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("tested_native_build", HERE / "native_build.py")
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class FailedRebuildPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lane = self.root / "lane"
        self.workspace = self.root / "ws"
        sell = self.workspace / BUILD.SELL_REL
        sell.parent.mkdir(parents=True)
        sell.write_text("synthetic sell source\n")
        self.harness = self.root / "harness"
        self.target = self.root / "target"
        self.harness.mkdir()
        self.target.mkdir()
        self.previous = self.lane / "out" / "attempt"
        self.previous.mkdir(parents=True)
        (self.previous / "candidate.so").write_bytes(b"last valid candidate")
        (self.previous / "build-record.json").write_text('{"returncode": 0}\n')

    def test_failed_rebuild_keeps_prior_valid_output_and_retains_new_log(self):
        def run(command, **options):
            if command[0] == 'rsync':
                return types.SimpleNamespace(returncode=0)
            options["stdout"].write(b"synthetic compiler failure\n")
            return types.SimpleNamespace(returncode=1)

        with patch.object(BUILD, "ensure_lane", return_value=(
                self.workspace, self.harness, self.target)), \
                patch.object(BUILD, "PRISTINE", self.root / "absent-pristine"), \
                patch.object(BUILD, "SDK", self.root / "sdk"), \
                patch.object(BUILD.subprocess, "run", side_effect=run):
            record = BUILD.build(self.lane, "attempt")

        self.assertEqual((self.previous / "candidate.so").read_bytes(), b"last valid candidate")
        self.assertEqual((self.previous / "build-record.json").read_text(), '{"returncode": 0}\n')
        failed_output = Path(record["output_dir"])
        self.assertNotEqual(failed_output, self.previous)
        self.assertEqual((failed_output / "build.log").read_text(), "synthetic compiler failure\n")
        self.assertEqual((failed_output / "build-record.json").read_text().count('"returncode": 1'), 1)

    def test_successful_rebuild_replaces_previous_output_after_staging(self):
        def run(command, **options):
            if command[0] == 'rsync':
                return types.SimpleNamespace(returncode=0)
            if Path(command[0]).name == 'cargo':
                target = Path(options["env"]["CARGO_TARGET_DIR"])
                artifact = target / "sbpf-solana-solana/release" / BUILD.PROGRAM
                artifact.parent.mkdir(parents=True)
                artifact.write_bytes(b"synthetic symbols")
            else:
                Path(command[-1]).write_bytes(b"synthetic candidate")
            return types.SimpleNamespace(returncode=0)

        with patch.object(BUILD, "ensure_lane", return_value=(
                self.workspace, self.harness, self.target)), \
                patch.object(BUILD, "PRISTINE", self.root / "absent-pristine"), \
                patch.object(BUILD, "SDK", self.root / "sdk"), \
                patch.object(BUILD.subprocess, "run", side_effect=run):
            record = BUILD.build(self.lane, "attempt")

        self.assertEqual(Path(record["output_dir"]), self.previous)
        self.assertEqual((self.previous / "candidate.so").read_bytes(), b"synthetic candidate")
        self.assertEqual((self.previous / "symbols.so").read_bytes(), b"synthetic symbols")
        self.assertFalse(list(self.previous.parent.glob(".attempt.*-*")))

    def test_exception_also_keeps_prior_output(self):
        def run(command, **options):
            if command[0] == 'rsync':
                return types.SimpleNamespace(returncode=0)
            options["stdout"].write(b"synthetic fatal failure\n")
            raise OSError("synthetic process failure")

        with patch.object(BUILD, "ensure_lane", return_value=(
                self.workspace, self.harness, self.target)), \
                patch.object(BUILD, "PRISTINE", self.root / "absent-pristine"), \
                patch.object(BUILD, "SDK", self.root / "sdk"), \
                patch.object(BUILD.subprocess, "run", side_effect=run):
            with self.assertRaisesRegex(OSError, "synthetic process failure"):
                BUILD.build(self.lane, "attempt")

        self.assertEqual((self.previous / "candidate.so").read_bytes(), b"last valid candidate")
        failed = list((self.previous.parent / ".failed").iterdir())
        self.assertEqual(len(failed), 1)
        self.assertEqual((failed[0] / "build.log").read_text(), "synthetic fatal failure\n")


if __name__ == "__main__":
    unittest.main()
