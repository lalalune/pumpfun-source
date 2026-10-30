#!/usr/bin/env python3
"""Focused fail-closed tests for the lifecycle comparator and plan."""

import copy
import unittest

import lifecycle


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


if __name__ == "__main__":
    unittest.main()
