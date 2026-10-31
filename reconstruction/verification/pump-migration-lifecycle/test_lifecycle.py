#!/usr/bin/env python3
"""Focused fail-closed tests for the lifecycle comparator and plan."""

import copy
import json
import struct
import unittest

import lifecycle
import verify


class LifecycleUnitTests(unittest.TestCase):
    def test_plan_and_oracle_have_identical_unique_membership(self):
        names = [case["name"] for case in lifecycle.scenarios()]
        self.assertEqual(len(names), 27)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(lifecycle.EXPECTED_OUTCOMES))

    def test_every_multistep_case_has_distinct_step_names(self):
        for case in lifecycle.scenarios():
            names = [step["name"] for step in case["steps"]]
            self.assertEqual(len(names), len(set(names)), case["name"])

    def test_semantic_logs_remove_only_declared_nondeterminism(self):
        logs = [
            "Program Pump invoke [1]",
            "Program log: AnchorError thrown in programs/pump/src/migrate.rs:1. Error Code: X.",
            "Program Pump consumed 12 of 20 compute units",
            "Program Pump failed: custom program error: 0x1",
        ]
        self.assertEqual(
            lifecycle.semantic_logs(logs),
            [
                "Program log: AnchorError thrown in src/migrate.rs:1. Error Code: X.",
                "Program Pump failed: custom program error: 0x1",
            ],
        )

    def test_compare_fails_closed_on_error_and_state(self):
        receipt = {field: None for field in lifecycle.STRICT_FIELDS}
        receipt.update(step="one", error=None, after={"a": 1})
        original = {"initial_state_hash": "same", "receipts": [receipt]}
        for field, value in (("error", "changed"), ("after", {"a": 2})):
            candidate = copy.deepcopy(original)
            candidate["receipts"][0][field] = value
            different, _ = lifecycle.compare_runs(original, candidate)
            self.assertIn("one:" + field, different)

    def test_compare_fails_closed_on_missing_receipt(self):
        original = {"initial_state_hash": "same", "receipts": [{"step": "one"}]}
        candidate = {"initial_state_hash": "same", "receipts": []}
        different, comparisons = lifecycle.compare_runs(original, candidate)
        self.assertEqual(different, ["receipt_count"])
        self.assertEqual(comparisons, [])

    def test_validate_rejects_receipt_without_signature_checks(self):
        receipt = {"step": "one", "signature": "sig", "signature_verification": [],
                   "error": "failed", "rollback_nonfee_equal": True, "outcome": "failed"}
        failures = lifecycle.validate_lifecycle({"receipts": [receipt]})
        self.assertIn("one:signature-verification", failures)

    def test_transfer_fee_layouts_are_well_formed(self):
        mint = bytearray(82)
        mint[45] = 1
        extended = lifecycle.transfer_fee_mint_data(mint, 100)
        self.assertEqual(len(extended), 278)
        self.assertEqual(extended[165], 1)
        self.assertEqual(extended[166:170], b"\x01\x00l\x00")
        account = lifecycle.token_account_data(lifecycle.STABLE_MINT, lifecycle.USER.pubkey(), 7, True)
        self.assertEqual(len(account), 178)
        self.assertEqual(account[165], 2)

    def test_transfer_fee_layout_regression_fails_closed(self):
        # The body-length gate used to be a bare assert, so python -O
        # stripped it and both images were compared against malformed mint
        # state. Shrink the packed fee once and require the explicit refusal.
        from unittest import mock

        original = struct.pack

        def narrow(fmt, *args):
            blob = original(fmt, *args)
            return blob[:-1] if fmt == "<QQH" else blob

        mint = bytearray(82)
        with mock.patch.object(lifecycle.struct, "pack", side_effect=narrow):
            with self.assertRaisesRegex(ValueError, "108 bytes"):
                lifecycle.transfer_fee_mint_data(mint, 100)

    def test_idl_inputs_decode_independently_of_the_host_locale(self):
        # evidence/upstream/pump.json contains U+2192 arrows ("SOL -> tokens");
        # a locale-default read cannot decode them on cp949 hosts, which made
        # this package unimportable there.
        self.assertIn("instructions", lifecycle.IDL)

    def test_report_fixture_field_matches_the_archived_posix_spelling(self):
        import gzip
        import pathlib

        archived = json.loads(gzip.decompress(
            (pathlib.Path(__file__).resolve().parent / "results/current-main.json.gz").read_bytes()))
        self.assertEqual(
            archived["fixture"],
            lifecycle.FIXTURE_PATH.relative_to(lifecycle.ROOT).as_posix())


class ReportOracleReceiptTests(unittest.TestCase):
    """Per-case oracle fields must agree with the receipts they summarize."""

    @classmethod
    def setUpClass(cls):
        cls.candidate = (lifecycle.ROOT / "evidence/original/pump/deployed.so").resolve()
        cls.report = lifecycle.run_suite(cls.candidate)
        cls.report["negative_controls"] = lifecycle.negative_control(cls.report)

    def problems_after(self, mutate):
        report = copy.deepcopy(self.report)
        mutate(report["cases"][0])
        return verify.verify(report, self.candidate)

    def test_unmodified_report_verifies(self):
        self.assertEqual(verify.verify(self.report, self.candidate), [])

    def test_contradicted_observed_outcomes_are_rejected(self):
        def mutate(row):
            row["observed_original_outcomes"] = ["ok"]

        self.assertIn("legacy/native-success-repeat:oracle_receipt",
                      self.problems_after(mutate))

    def test_invented_oracle_mismatches_are_rejected(self):
        def mutate(row):
            row["oracle_mismatches"] = [{"expected": ["ok"], "observed": ["ok"]}]

        self.assertIn("legacy/native-success-repeat:oracle_receipt",
                      self.problems_after(mutate))


if __name__ == "__main__":
    unittest.main()
