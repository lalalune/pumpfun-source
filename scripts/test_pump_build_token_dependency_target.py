"""The clean-target admission must cover the directory each dependency builds into.

token_metadata is built from its own workspace and its ELF is read from
programs/token-metadata/target/deploy, not from the checkout's root target.
"""

from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().with_name("pump_build_token_dependency.py")
COMMITS = {
    "spl_token": "a94dd19750dc3b2409f73e15bb74754935b2a489",
    "token_metadata": "17e99434af5ead3e989c08f32af33609821d0bc0",
}


class ReachedDocker(Exception):
    pass


def admit(dependency, source, output):
    """Return None once every source check passes, or the refused message."""

    def check_output(command, **_):
        return {"rev-parse": COMMITS[dependency] + "\n"}.get(command[3], "")

    argv = [str(SCRIPT), "--dependency", dependency, "--source", str(source), "--output", str(output)]
    with mock.patch.object(sys, "argv", argv), \
            mock.patch.object(subprocess, "check_output", side_effect=check_output), \
            mock.patch.object(subprocess, "run", side_effect=ReachedDocker):
        try:
            runpy.run_path(str(SCRIPT), run_name="__main__")
        except ReachedDocker:
            return None
        except AssertionError as error:
            return str(error)
    raise RuntimeError("the builder returned without reaching docker")


class BuildTargetAdmissionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "source"
        self.source.mkdir()
        self.output = Path(directory.name) / "output"

    def test_token_metadata_refuses_its_workspace_target(self):
        stale = self.source / "programs/token-metadata/target/deploy"
        stale.mkdir(parents=True)
        (stale / "token_metadata.so").write_bytes(b"earlier build")
        self.assertEqual(admit("token_metadata", self.source, self.output),
                         "require a clean build target")

    def test_token_metadata_still_refuses_a_root_target(self):
        (self.source / "target").mkdir()
        self.assertEqual(admit("token_metadata", self.source, self.output),
                         "require a clean build target")

    def test_root_workspace_dependency_refuses_a_root_target(self):
        (self.source / "target").mkdir()
        self.assertEqual(admit("spl_token", self.source, self.output),
                         "require a clean build target")

    def test_fresh_checkouts_are_admitted(self):
        (self.source / "programs/token-metadata").mkdir(parents=True)
        self.assertIsNone(admit("token_metadata", self.source, self.output))
        self.assertIsNone(admit("spl_token", self.source, self.output.with_name("other")))


if __name__ == "__main__":
    unittest.main()
