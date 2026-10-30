#!/usr/bin/env python3
"""Every link inside an authenticated vendor package must count as an undeclared member."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
from pathlib import Path
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("mayhem_native_linux_vendor_links", HERE / "build_linux.py")
native = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(native)


class VendorFileLinkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="mayhem-vendor-links-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.vendor = self.root / "vendor"
        self.controller = self.root / "controller"
        self.controller.mkdir()
        self.package = self.vendor / "example-1.0.0"
        source = self.package / "src/lib.rs"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"pub fn answer() -> u8 { 42 }\n")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        (self.package / ".cargo-checksum.json").write_text(
            json.dumps({"package": "a" * 64, "files": {"src/lib.rs": digest}})
        )
        records = {"packages": [{"directory": "example-1.0.0", "package_sha256": "a" * 64, "file_count": 1}]}
        (self.controller / "vendor-inputs.json").write_text(json.dumps(records))
        self.expected = native.inspect_vendor(self.vendor, self.controller)["closure_sha256"]

    def assert_rejected(self):
        with self.assertRaisesRegex(ValueError, "vendor file set differs"):
            native.check_vendor(self.vendor, self.controller, self.expected)

    def test_dangling_link_is_rejected(self):
        (self.package / "src/generated.rs").symlink_to("missing.rs")
        self.assert_rejected()

    def test_directory_link_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "extra.rs").write_bytes(b"pub const EXTRA: u8 = 1;\n")
        (self.package / "src/extra").symlink_to(outside, target_is_directory=True)
        self.assert_rejected()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_fifo_is_rejected(self):
        os.mkfifo(self.package / "src/pipe")
        self.assert_rejected()

    def test_real_empty_directory_is_still_admitted(self):
        (self.package / "src/empty").mkdir()
        self.assertEqual(native.check_vendor(self.vendor, self.controller, self.expected)["packages"], 1)

    def test_nested_checksum_basename_is_not_hidden(self):
        hidden = self.package / "src/.cargo-checksum.json"
        for kind in ("file", "dangling-link", "directory-link"):
            with self.subTest(kind=kind):
                if kind == "file":
                    hidden.write_bytes(b"undeclared")
                else:
                    hidden.symlink_to("missing" if kind == "dangling-link" else self.controller,
                                      target_is_directory=kind == "directory-link")
                try:
                    self.assert_rejected()
                finally:
                    hidden.unlink()

    def test_declared_nested_checksum_file_keeps_receipt_encoding(self):
        extra = self.package / "src/.cargo-checksum.json"
        extra.write_bytes(b"declared source data")
        checksum = self.package / ".cargo-checksum.json"
        data = json.loads(checksum.read_bytes())
        data["files"]["src/.cargo-checksum.json"] = hashlib.sha256(extra.read_bytes()).hexdigest()
        checksum.write_text(json.dumps(data))
        records = json.loads((self.controller / "vendor-inputs.json").read_bytes())
        records["packages"][0]["file_count"] = 2
        (self.controller / "vendor-inputs.json").write_text(json.dumps(records))
        closure = [{"directory": "example-1.0.0", "package_sha256": "a" * 64, "files": data["files"]}]
        expected = hashlib.sha256(json.dumps(closure, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(native.check_vendor(self.vendor, self.controller, expected),
                         {"packages": 1, "closure_sha256": expected})
        extra.write_bytes(b"tampered source data")
        with self.assertRaisesRegex(ValueError, "vendor byte differs"):
            native.check_vendor(self.vendor, self.controller, expected)

    def test_declared_file_link_is_rejected_without_reading_target(self):
        source = self.package / "src/lib.rs"
        outside = self.root / "outside.rs"
        outside.write_bytes(source.read_bytes())
        source.unlink()
        source.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "nonregular vendor file"):
            native.check_vendor(self.vendor, self.controller, self.expected)
        self.assertEqual(outside.read_bytes(), b"pub fn answer() -> u8 { 42 }\n")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX FIFOs")
    def test_declared_fifo_is_rejected_before_hashing(self):
        source = self.package / "src/lib.rs"
        source.unlink()
        os.mkfifo(source)
        with self.assertRaisesRegex(ValueError, "nonregular vendor file"):
            native.check_vendor(self.vendor, self.controller, self.expected)

    @unittest.skipUnless(hasattr(socket, "AF_UNIX"), "requires Unix sockets")
    def test_unlisted_socket_is_rejected(self):
        previous = Path.cwd()
        try:
            # macOS limits Unix socket paths to 104 bytes. Bind relative to
            # the package so the test does not depend on tempfile root length.
            os.chdir(self.package / "src")
            with socket.socket(socket.AF_UNIX) as server:
                server.bind("socket")
                self.assert_rejected()
        finally:
            os.chdir(previous)

    def test_declared_package_directory_link_is_rejected(self):
        outside = self.root / "outside-package"
        self.package.rename(outside)
        self.package.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "nonregular vendor package"):
            native.check_vendor(self.vendor, self.controller, self.expected)
        self.assertEqual((outside / "src/lib.rs").read_bytes(), b"pub fn answer() -> u8 { 42 }\n")

    def test_directory_read_error_is_not_silently_ignored(self):
        hidden = self.package / "unreadable"
        hidden.mkdir()
        scan = os.scandir
        def unreadable(path):
            if Path(path) == hidden:
                raise PermissionError("controlled unreadable vendor directory")
            return scan(path)
        with mock.patch.object(native.os, "scandir", side_effect=unreadable):
            with self.assertRaisesRegex(PermissionError, "controlled unreadable"):
                native.check_vendor(self.vendor, self.controller, self.expected)


if __name__ == "__main__":
    unittest.main()
