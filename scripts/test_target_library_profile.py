#!/usr/bin/env python3
"""Admission tests for hash-bound target-library profiles."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_target_library_profile as profile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Fixture:
    def __init__(self, root, rustc_body):
        self.root = Path(root).resolve()
        self.native = self.root / "native"
        self.output = self.root / "profile-sdk"
        self.libraries = self.root / "libraries"
        self.spec_path = self.root / "profile.json"
        (self.native / "rust/bin").mkdir(parents=True)
        (self.native / "rust/lib/rustlib/sbf-solana-solana/lib").mkdir(parents=True)
        self.rustc = self.native / "rust/bin/rustc"
        self.cargo = self.native / "rust/bin/cargo"
        self.rustc.write_text(rustc_body)
        self.rustc.chmod(0o755)
        self.cargo.write_text("cargo")
        (self.native / "rust/lib/rustlib/sbf-solana-solana/lib/placeholder.txt").write_text("old")
        self.libraries.mkdir()
        (self.libraries / "libtest.so").write_text("library")
        (self.libraries / "self-contained").mkdir()
        self.spec = {
            "name": "linux-v1.44-sbf",
            "target": "sbf-solana-solana",
            "scope": "synthetic profile admission test",
            "target_libraries": {
                path.name: sha(path)
                for path in self.libraries.iterdir()
                if path.is_file()
            },
            "empty_directories": ["self-contained"],
            "native_tools": {
                "rust/bin/rustc": sha(self.rustc),
                "rust/bin/cargo": sha(self.cargo),
            },
        }
        self.spec_path.write_text(json.dumps(self.spec))

    def specification(self):
        return mock.patch.object(
            profile, "specification", return_value=(self.spec_path, self.spec)
        )

    def prepare(self):
        return profile.prepare(
            "linux-v1.44-sbf", self.native, self.libraries, self.output
        )


class ProfileAdmissionTests(unittest.TestCase):
    def test_rejected_compiler_fails_without_publishing_a_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(
                temporary,
                '#!/bin/sh\nprintf "%s\\n" "unexpected compiler output"\n',
            )
            with fixture.specification(), self.assertRaises(AssertionError):
                fixture.prepare()
            manifest = fixture.output.parent / "target-library-profile-files.json"
            self.assertFalse(
                manifest.exists(),
                "a rejected compiler must not leave an admitted-profile manifest",
            )

    def test_verified_profile_publishes_and_rechecks_the_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(temporary, "")
            fixture.rustc.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "--print" ] && [ "$2" = "sysroot" ]; then\n'
                f"  printf '%s\\n' '{fixture.output}/rust'\n"
                "  exit 0\n"
                "fi\n"
                'if [ "$1" = "--print" ] && [ "$2" = "target-libdir" ]; then\n'
                f"  printf '%s\\n' '{fixture.output}/rust/lib/rustlib/sbf-solana-solana/lib'\n"
                "  exit 0\n"
                "fi\n"
                "exit 2\n"
            )
            fixture.rustc.chmod(0o755)
            fixture.spec["native_tools"]["rust/bin/rustc"] = sha(fixture.rustc)
            fixture.spec_path.write_text(json.dumps(fixture.spec))
            with fixture.specification():
                _, record = fixture.prepare()
                manifest = Path(record["file_manifest"])
                self.assertEqual(record["status"], "verified")
                self.assertTrue(manifest.is_file())
                self.assertEqual(sha(manifest), record["file_manifest_sha256"])
                rechecked = profile.finish(record)
            self.assertEqual(rechecked["status"], "verified")
            self.assertEqual(
                rechecked["file_manifest_sha256"], record["file_manifest_sha256"]
            )


if __name__ == "__main__":
    unittest.main()
