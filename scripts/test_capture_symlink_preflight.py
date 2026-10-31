#!/usr/bin/env python3
"""Capture must refuse a symlinked output and retain prior evidence."""
import base64
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import capture


class CaptureSymlinkPreflightTests(unittest.TestCase):
    def account(self, payload):
        return {
            "context": {"slot": 41},
            "value": {
                "owner": "BPFLoader2111111111111111111111111111111111",
                "executable": True,
                "data": [base64.b64encode(payload).decode("ascii")],
            },
        }

    def patch(self):
        payload = b"\x7fELF" + bytes(60)
        account = self.account(payload)
        return (
            mock.patch.object(capture, "account", side_effect=[(account, payload), (account, payload)]),
            mock.patch.object(capture, "rpc", return_value="genesis"),
        )

    def test_dangling_symlink_target_is_not_created(self):
        with tempfile.TemporaryDirectory(prefix="capture-symlink-") as directory:
            root = Path(directory)
            escaped = root / "escaped"
            output = root / "pump"
            try:
                output.symlink_to(escaped)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks are unavailable: {error}")
            account_patch, rpc_patch = self.patch()
            with account_patch, rpc_patch:
                with self.assertRaisesRegex(FileExistsError, "already exists"):
                    capture.capture("https://rpc.invalid", "pump", "program", output)
            self.assertFalse(escaped.exists())
            self.assertTrue(output.is_symlink())

    def test_existing_capture_is_not_replaced(self):
        with tempfile.TemporaryDirectory(prefix="capture-existing-") as directory:
            output = Path(directory) / "pump"
            output.write_bytes(b"prior capture\n")
            account_patch, rpc_patch = self.patch()
            with account_patch, rpc_patch:
                with self.assertRaisesRegex(FileExistsError, "already exists"):
                    capture.capture("https://rpc.invalid", "pump", "program", output)
            self.assertEqual(output.read_bytes(), b"prior capture\n")

    def test_fresh_output_succeeds(self):
        with tempfile.TemporaryDirectory(prefix="capture-fresh-") as directory:
            output = Path(directory) / "pump"
            account_patch, rpc_patch = self.patch()
            with account_patch, rpc_patch:
                capture.capture("https://rpc.invalid", "pump", "program", output)
            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"capture.json", "deployed.so", "program-account.bin"},
            )


if __name__ == "__main__":
    unittest.main()
