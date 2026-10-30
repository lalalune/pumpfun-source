#!/usr/bin/env python3
"""The constant-product comparison slices its original range from a pinned capture."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "pump_build_constant_product.py"
END = 0x88908


def fixture_root(blob, manifest_sha=None):
    """A repository fixture holding the builder and a captured pump image."""
    temporary = Path(tempfile.mkdtemp(prefix="constant-product-pin-"))
    (temporary / "scripts").mkdir()
    shutil.copy(SCRIPTS / SCRIPT, temporary / "scripts" / SCRIPT)
    (temporary / "evidence/original/pump").mkdir(parents=True)
    (temporary / "evidence/original/pump/deployed.so").write_bytes(blob)
    sha = manifest_sha or hashlib.sha256(blob).hexdigest()
    (temporary / "evidence/original/pump/capture.json").write_text(
        json.dumps({"payload_sha256": sha}))
    return temporary


def run_builder(root):
    return subprocess.run(
        [sys.executable, str(root / "scripts" / SCRIPT),
         "--toolchain", "unused-toolchain", "--output", str(root / "out")],
        capture_output=True, text=True)


class PinnedOriginalTests(unittest.TestCase):
    def test_capture_missing_the_manifest_sha_is_rejected_before_building(self):
        root = fixture_root(bytearray(END), manifest_sha="0" * 64)
        completed = run_builder(root)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("does not match its retained capture manifest", completed.stderr)
        self.assertFalse((root / "out/build.log").exists())

    def test_capture_shorter_than_the_range_is_rejected_before_building(self):
        root = fixture_root(bytearray(END - 8))
        completed = run_builder(root)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("shorter than the pinned original function range", completed.stderr)
        self.assertFalse((root / "out/build.log").exists())
        # The unpinned slice this replaces silently returned 8 bytes short.
        blob = (root / "evidence/original/pump/deployed.so").read_bytes()
        self.assertEqual(len(blob[0x880b0:END]), END - 0x880b0 - 8)

    def test_pinned_capture_proceeds_to_the_build(self):
        blob = bytearray(END)
        blob[0x880b0:0x880b0 + 14] = b"fragment-bytes"
        root = fixture_root(bytes(blob))
        completed = run_builder(root)
        # Pinning passed: the run reaches the (absent) toolchain launcher
        # instead of refusing the capture.
        self.assertNotIn("retained capture manifest", completed.stderr)
        self.assertNotIn("shorter than", completed.stderr)
        self.assertIn("subprocess", completed.stderr)


if __name__ == "__main__":
    unittest.main()
