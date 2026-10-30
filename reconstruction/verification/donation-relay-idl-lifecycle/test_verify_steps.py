from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("relay_idl_verify_steps", HERE / "verify_report.py")
assert SPEC and SPEC.loader
verify_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_report)


class EmptyCaseTests(unittest.TestCase):
    def report(self, root: Path, candidate: Path) -> dict:
        source_rows, source_digest = verify_report.manifest(root / "programs/donation-relay", root)
        package_rows = {path.relative_to(root).as_posix(): verify_report.file_sha(path)
                        for path in sorted(HERE.iterdir()) if path.is_file()}
        cases = [{"name": name, "classification": "equal_observed_behavior", "problems": [], "steps": []}
                 for name in ("stateful_lifecycle", "admission_matrix")]
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
            "cases": cases,
            "case_count": 2,
            "matching_cases": 2,
            "different_cases": 0,
            "transaction_identity": {"transaction_count": 0, "unique_transaction_count": 0,
                                     "all_transactions_signature_verified": True},
            "negative_controls": {"detected": {"account_state": True, "error": True, "event_payload": True},
                                  "all_detected": True},
            "supported_operations": ["Create", "CreateBuffer", "Write", "SetBuffer", "SetAuthority", "Close", "Resize"],
        }

    def test_planned_cases_without_transactions_are_rejected(self) -> None:
        root = HERE.parents[2]
        candidate = root / "evidence/dependencies/donation_relay/deployed.so"
        problems = verify_report.validate(self.report(root, candidate), root, candidate)
        self.assertEqual(problems, ["case_steps"])

    def test_one_empty_case_is_rejected(self) -> None:
        root = HERE.parents[2]
        candidate = root / "evidence/dependencies/donation_relay/deployed.so"
        report = self.report(root, candidate)
        report["cases"][0]["steps"] = [{
            "name": "only", "signature": "s", "signature_verified": True,
            "original": {"error": None, "logs": [], "events": [], "inner_instructions": [],
                         "return_data": None, "before": {}, "after": {}},
            "candidate": {"error": None, "logs": [], "events": [], "inner_instructions": [],
                          "return_data": None, "before": {}, "after": {}},
        }]
        report["transaction_identity"].update(transaction_count=1, unique_transaction_count=1)
        self.assertIn("case_steps", verify_report.validate(report, root, candidate))


if __name__ == "__main__":
    unittest.main()
