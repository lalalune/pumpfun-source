#!/usr/bin/env python3
"""The authenticated vendor directory must hold exactly the declared packages."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("mayhem_native_linux_vendor", HERE / "build_linux.py")
native = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(native)


def write_package(vendor: Path, name: str) -> None:
    source = vendor / name / "src/lib.rs"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"pub fn answer() -> u8 { 42 }\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    checksum = {"package": "a" * 64, "files": {"src/lib.rs": digest}}
    (vendor / name / ".cargo-checksum.json").write_text(json.dumps(checksum))


class VendorMembershipTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mayhem-vendor-members-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.vendor = self.root / "vendor"
        self.controller = self.root / "controller"
        self.controller.mkdir()
        write_package(self.vendor, "example-1.0.0")
        records = {"packages": [{"directory": "example-1.0.0", "package_sha256": "a" * 64, "file_count": 1}]}
        (self.controller / "vendor-inputs.json").write_text(json.dumps(records))
        self.expected = native.inspect_vendor(self.vendor, self.controller)["closure_sha256"]

    def rejected(self) -> bool:
        try:
            native.check_vendor(self.vendor, self.controller, self.expected)
        except ValueError as error:
            self.assertIn("vendor package set differs", str(error))
            return True
        return False

    def test_declared_packages_are_admitted(self):
        self.assertEqual(native.check_vendor(self.vendor, self.controller, self.expected)["packages"], 1)

    def test_undeclared_package_is_rejected(self):
        write_package(self.vendor, "undeclared-9.9.9")
        self.assertTrue(self.rejected(), "undeclared vendor package was admitted")

    def test_undeclared_symlink_is_rejected(self):
        (self.vendor / "alias-1.0.0").symlink_to("example-1.0.0", target_is_directory=True)
        self.assertTrue(self.rejected(), "undeclared vendor alias was admitted")


if __name__ == "__main__":
    unittest.main()
