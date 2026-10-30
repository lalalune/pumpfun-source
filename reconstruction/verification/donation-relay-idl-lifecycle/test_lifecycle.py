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

    @staticmethod
    def matching_step():
        import copy
        row = {
            "error": None,
            "logs": ["Program log: reserved", "Program consumed: 1 of 1400000 compute units"],
            "events": ["Program data: event"],
            "inner_instructions": [],
            "return_data": [None, ""],
            "before": {"SomeAccount11111111111111111111111111111111": {"lamports": 1}},
            "after": {"SomeAccount11111111111111111111111111111111": {"lamports": 2}},
        }
        return {"original": row, "candidate": copy.deepcopy(row)}

    def test_comparator_controls_replay_mutations_through_the_case_comparison(self) -> None:
        controls = producer.comparator_controls(self.matching_step())
        self.assertTrue(controls["all_detected"])
        self.assertEqual(controls["detected"],
                         {"account_state": True, "error": True, "event_payload": True})

    def test_comparator_controls_fail_when_the_comparison_stops_reporting(self) -> None:
        from unittest import mock
        with mock.patch.object(producer.Pair, "_comparable", staticmethod(lambda row: {})):
            controls = producer.comparator_controls(self.matching_step())
        self.assertFalse(controls["all_detected"])
        self.assertEqual(controls["detected"],
                         {"account_state": False, "error": False, "event_payload": False})

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


VSPEC = importlib.util.spec_from_file_location("relay_idl_verify_report", HERE / "verify_report.py")
assert VSPEC and VSPEC.loader
verify_report = importlib.util.module_from_spec(VSPEC)
VSPEC.loader.exec_module(verify_report)


class VerifyReportTests(unittest.TestCase):
    def vacuous_report(self, root: Path, candidate: Path) -> dict:
        source_rows, source_digest = verify_report.manifest(root / "programs/donation-relay", root)
        package_rows = {str(path.relative_to(root)): verify_report.file_sha(path) for path in sorted(HERE.iterdir()) if path.is_file()}
        return {
            "schema": "donation-relay-idl-lifecycle-v1",
            "program": verify_report.RELAY,
            "inputs": {
                "captured_elf": {"sha256": verify_report.ORIGINAL_SHA256},
                "candidate_elf": {"sha256": verify_report.file_sha(candidate)},
                "source_manifest_sha256": source_digest,
                "source_files": source_rows,
                "test_package_files": package_rows,
            },
            "cases": [],
            "case_count": 0,
            "matching_cases": 0,
            "different_cases": 0,
            "transaction_identity": {"transaction_count": 0, "unique_transaction_count": 0, "all_transactions_signature_verified": True},
            "negative_controls": {"detected": {}, "all_detected": True},
            "supported_operations": ["Create", "CreateBuffer", "Write", "SetBuffer", "SetAuthority", "Close", "Resize"],
        }

    def test_report_without_planned_cases_or_controls_is_rejected(self) -> None:
        root = HERE.parents[2]
        candidate = root / "evidence/dependencies/donation_relay/deployed.so"
        problems = verify_report.validate(self.vacuous_report(root, candidate), root, candidate)
        self.assertIn("case_membership", problems)
        self.assertIn("negative_control_membership", problems)


if __name__ == "__main__":
    unittest.main()
