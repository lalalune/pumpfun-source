from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("relay_idl_lifecycle", HERE / "producer.py")
assert SPEC and SPEC.loader
producer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = producer
SPEC.loader.exec_module(producer)


class LifecycleUnitTests(unittest.TestCase):
    def test_authentic_selector_and_header(self) -> None:
        self.assertEqual(producer.IDL_SELECTOR.hex(), "40f4bc78a7e9690a")
        authority = producer.owned_key("unit", "authority").pubkey()
        data = producer.idl_data(authority, 9, b"abc")
        self.assertEqual(len(data), producer.HEADER_LEN + 9)
        decoded = producer.decode_idl(data)
        self.assertEqual(decoded["authority"], str(authority))
        self.assertEqual(decoded["data_len"], 3)

    def test_canonical_address_is_stable(self) -> None:
        first = producer.idl_address()
        second = producer.idl_address()
        self.assertEqual(first, second)
        self.assertNotEqual(first[0], first[1])

    def test_comparator_controls_detect_all_dimensions(self) -> None:
        controls = producer.comparator_controls()
        self.assertTrue(controls["all_detected"])
        self.assertEqual(set(controls["detected"]), {"account_state", "error", "event_payload"})

    def test_output_refuses_overwrite_before_execution(self) -> None:
        root = HERE.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            output.write_text("retained\n")
            with self.assertRaisesRegex(SystemExit, "refusing to overwrite"):
                producer.execute(root, Path(directory) / "candidate.so", output)
            self.assertEqual(output.read_text(), "retained\n")

    def test_missing_candidate_is_infrastructure_error(self) -> None:
        root = HERE.parents[2]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            with self.assertRaisesRegex(SystemExit, "candidate does not exist"):
                producer.execute(root, Path(directory) / "missing.so", output)
            self.assertFalse(output.exists())

    def test_source_manifest_changes_when_input_changes(self) -> None:
        root = HERE.parents[2]
        rows, digest = producer.source_manifest(root)
        self.assertIn("programs/donation-relay/Cargo.toml", rows)
        with mock.patch.object(producer, "file_sha", side_effect=lambda path: "0" * 64 if path.name == "Cargo.toml" else producer.sha(path.read_bytes())):
            _, changed = producer.source_manifest(root)
        self.assertNotEqual(digest, changed)


if __name__ == "__main__":
    unittest.main()
