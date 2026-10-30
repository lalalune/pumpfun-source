"""Synthetic regressions for repeated dependency builds in one Docker container."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "search_dependency_commit", ROOT / "scripts/search_dependency_commit.py"
)
search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(search)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dependency-search-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / "output"
        self.source = self.output / "src"
        self.artifact = self.source / "target/deploy/spl_associated_token_account.so"
        self.binary = b"synthetic captured dependency ELF"
        evidence = self.root / "evidence/dependencies/associated_token"
        evidence.mkdir(parents=True)
        (evidence / "deployed.so").write_bytes(self.binary)
        self.current_commit = None
        self.host_clean_failures = 0
        self.container_cleans = 0
        self.container_clean_commands = []
        self.container_clean_returncode = 0
        self.builds = []

    def completed(self, command, returncode=0, stdout="", stderr=""):
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    def fake_read(self, command):
        if command[-1] == "pwd":
            return "/work"
        if "sleep" in command:
            return "container-1"
        if "rustup" in command:
            return "stable"
        if command[0:3] == ["git", "-C", str(self.source)] and "rev-parse" in command:
            return self.current_commit
        raise AssertionError("unexpected read command: " + repr(command))

    def fake_run(self, command, **kwargs):
        command = [str(item) for item in command]
        if command[:2] == ["git", "clone"]:
            self.source.mkdir(parents=True)
            return self.completed(command)
        if command[:3] == ["git", "-C", str(self.source)]:
            operation = command[3]
            if operation == "fetch":
                return self.completed(command)
            if operation == "reset":
                return self.completed(command)
            if operation == "clean":
                self.host_clean_failures += 1
                return self.completed(
                    command,
                    returncode=1,
                    stderr="target is owned by container root",
                )
            if operation == "checkout":
                self.current_commit = command[-1].removesuffix("^{commit}")
                return self.completed(command)
        if command[:2] == ["docker", "pull"]:
            return self.completed(command)
        if command[:2] == ["docker", "stop"]:
            return self.completed(command)
        if (
            command[:3] == ["docker", "exec", "--user"]
            and command[3] == "0:0"
            and "git" in command
            and command[-2:] == ["clean", "-fdxq"]
        ):
            self.container_cleans += 1
            self.container_clean_commands.append(command)
            if self.container_clean_returncode == 0:
                self.artifact.unlink(missing_ok=True)
            return self.completed(
                command,
                returncode=self.container_clean_returncode,
                stderr="container cleanup failed",
            )
        if "cargo" in command:
            self.builds.append(self.current_commit)
            if self.current_commit == "commit-1":
                self.artifact.parent.mkdir(parents=True)
                self.artifact.write_bytes(self.binary)
            return self.completed(command)
        raise AssertionError("unexpected run command: " + repr(command))

    def execute(self):
        argv = [
            "search_dependency_commit.py",
            "--dependency",
            "associated_token",
            "--commits",
            "commit-1",
            "commit-2",
            "--output",
            str(self.output),
        ]
        stdout = io.StringIO()
        with mock.patch.object(search, "ROOT", self.root), mock.patch.object(
            search, "read", side_effect=self.fake_read
        ), mock.patch.object(
            search,
            "subprocess",
            types.SimpleNamespace(run=self.fake_run, DEVNULL=subprocess.DEVNULL),
        ), mock.patch.object(
            sys, "argv", argv
        ), contextlib.redirect_stdout(stdout):
            search.main()
        return stdout.getvalue()

    def test_failed_host_cleanup_cannot_reuse_previous_commit_artifact(self):
        self.execute()
        report = json.loads((self.output / "search-report.json").read_text())

        self.assertEqual(self.builds, ["commit-1", "commit-2"])
        self.assertEqual(len(report["matches"]), 1)
        self.assertTrue(report["results"][0]["full_byte_equality"])
        self.assertFalse(report["results"][1].get("full_byte_equality", False))
        self.assertFalse(report["results"][1]["built"])
        self.assertTrue(report["results"][1]["artifact_missing"])
        self.assertEqual(self.host_clean_failures, 2)
        self.assertEqual(self.container_cleans, 2)
        for command in self.container_clean_commands:
            self.assertIn("-c", command)
            self.assertIn("safe.directory=/work", command)

    def test_container_cleanup_failure_stops_before_checkout(self):
        self.container_clean_returncode = 1
        with self.assertRaisesRegex(RuntimeError, "container cleanup failed"):
            self.execute()

        self.assertEqual(self.host_clean_failures, 1)
        self.assertEqual(self.container_cleans, 1)
        self.assertEqual(self.builds, [])
        self.assertFalse((self.output / "search-report.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
