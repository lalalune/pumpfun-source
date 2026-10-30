"""Failed RPC captures must not publish partial evidence directories."""

import base64
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


if __name__ == "__main__":
    unittest.main()
