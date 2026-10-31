"""Failed RPC captures must not publish partial evidence directories."""

import base64
import contextlib
import errno
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import capture


class CapturePublicationTests(unittest.TestCase):
    def account(self, payload):
        return {
            "context": {"slot": 41},
            "value": {
                "owner": "BPFLoader2111111111111111111111111111111111",
                "executable": True,
                "data": [base64.b64encode(payload).decode("ascii")],
            },
        }

    def test_failure_after_payload_write_leaves_no_partial_capture(self):
        payload = b"\x7fELF" + bytes(60)
        account = self.account(payload)
        with tempfile.TemporaryDirectory(prefix="capture-atomicity-") as directory:
            output = Path(directory) / "pump"
            with (
                mock.patch.object(
                    capture, "account", side_effect=[(account, payload), (account, payload)]
                ),
                mock.patch.object(
                    capture, "rpc", side_effect=RuntimeError("genesis RPC failed")
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "genesis RPC failed"):
                    capture.capture("https://rpc.invalid", "pump", "program", output)

            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.iterdir()), [])

    def test_success_publishes_complete_capture_without_staging_directory(self):
        payload = b"\x7fELF" + bytes(60)
        account = self.account(payload)
        with tempfile.TemporaryDirectory(prefix="capture-atomicity-") as directory:
            output = Path(directory) / "pump"
            with (
                mock.patch.object(
                    capture, "account", side_effect=[(account, payload), (account, payload)]
                ),
                mock.patch.object(capture, "rpc", return_value="genesis"),
            ):
                capture.capture("https://rpc.invalid", "pump", "program", output)

            self.assertEqual(
                {path.name for path in output.iterdir()},
                {"capture.json", "deployed.so", "program-account.bin"},
            )
            self.assertEqual(list(output.parent.glob(".pump.capture-*")), [])

    @unittest.skipUnless(
        os.name == "nt" or sys.platform == "darwin" or sys.platform.startswith("linux"),
        "native no-replace directory publication requires Windows, macOS or Linux",
    )
    def test_concurrent_empty_destination_is_not_replaced(self):
        # Supply real retained bytes at the RPC boundary. All capture writes,
        # existence checks and the final native publication still run normally.
        source = Path(__file__).resolve().parents[1] / "evidence/dependencies/associated_token"
        payload = (source / "deployed.so").read_bytes()
        record = json.loads((source / "capture.json").read_text(encoding="utf-8"))
        account = self.account(payload)
        native_exists = Path.exists
        with tempfile.TemporaryDirectory(prefix="capture-race-") as directory:
            output = Path(directory) / "associated_token"
            observations = []
            checks = 0

            def create_competing_directory_after_check(path):
                nonlocal checks
                existed = native_exists(path)
                if path == output:
                    checks += 1
                    if checks == 2:
                        self.assertFalse(existed)
                        # Schedule the other writer immediately after the final
                        # real absent observation; do not mock the rename.
                        output.mkdir()
                        metadata = output.stat()
                        observations.append((metadata.st_dev, metadata.st_ino))
                return existed

            with (
                mock.patch.object(capture, "account", side_effect=[(account, payload), (account, payload)]),
                mock.patch.object(capture, "rpc", return_value=record["genesis_hash"]),
                mock.patch.object(Path, "exists", create_competing_directory_after_check),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(FileExistsError):
                    capture.capture("https://rpc.invalid", "associated_token", record["program"], output)

            metadata = output.stat()
            self.assertEqual(observations, [(metadata.st_dev, metadata.st_ino)])
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(output.parent.iterdir()), [output])

    @unittest.skipIf(os.name == "nt", "Windows provides native no-replace publication")
    def test_unsupported_no_replace_cleans_up_without_publishing(self):
        import deep_disassembly as publication

        payload = b"\x7fELF" + bytes(60)
        account = self.account(payload)
        with tempfile.TemporaryDirectory(prefix="capture-unsupported-") as directory:
            output = Path(directory) / "pump"
            with (
                mock.patch.object(capture, "account", side_effect=[(account, payload), (account, payload)]),
                mock.patch.object(capture, "rpc", return_value="genesis"),
                mock.patch.object(publication.sys, "platform", "unsupported"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                with self.assertRaises(OSError) as error:
                    capture.capture("https://rpc.invalid", "pump", "program", output)

            self.assertEqual(error.exception.errno, errno.ENOTSUP)
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.iterdir()), [])

    def test_success_does_not_remove_reused_staging_name(self):
        import deep_disassembly as publication

        payload = (Path(__file__).resolve().parents[1]
                   / 'evidence/dependencies/associated_token/deployed.so').read_bytes()
        account = self.account(payload)
        native_rename = publication.rename_directory
        reused = []
        def publish_then_reuse(source, destination):
            native_rename(source, destination)
            source.mkdir()
            (source / 'other-writer').write_bytes(b'retained')
            reused.append(source)
        with tempfile.TemporaryDirectory(prefix='capture-staging-owner-') as directory:
            output = Path(directory) / 'associated_token'
            with (
                mock.patch.object(capture, 'account', side_effect=[(account, payload), (account, payload)]),
                mock.patch.object(capture, 'rpc', return_value='genesis'),
                mock.patch.object(publication, 'rename_directory', side_effect=publish_then_reuse),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                capture.capture('https://rpc.invalid', 'associated_token', 'program', output)
            self.assertEqual((output / 'deployed.so').read_bytes(), payload)
            self.assertEqual((reused[0] / 'other-writer').read_bytes(), b'retained')


if __name__ == "__main__":
    unittest.main()
