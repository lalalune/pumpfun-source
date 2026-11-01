#!/usr/bin/env python3
import copy
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("admin_cto_lifecycle", HERE / "lifecycle.py")
life = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = life
SPEC.loader.exec_module(life)


class LifecycleTests(unittest.TestCase):
    def test_keys_are_authentic_and_distinct(self):
        keys = [life.PAYER, life.ADMIN, *life.CREATORS]
        self.assertEqual(len({key.pubkey() for key in keys}), len(keys))
        self.assertTrue(all(bytes(key) for key in keys))

    def test_plan_is_stateful_and_covers_requested_families(self):
        cases = life.scenarios()
        self.assertEqual(len(cases), 9)
        self.assertEqual(sum(len(case["steps"]) for case in cases), 20)
        names = " ".join(case["name"] for case in cases)
        for word in ("native", "spl", "token22", "holder", "sharing", "frozen", "cross-mint", "atomic"):
            self.assertIn(word, names)
        self.assertTrue(any(len(case["steps"]) >= 3 for case in cases))

    def test_fixture_uses_canonical_addresses(self):
        mint = life.Harness._mint_fixture(0, "native")
        self.assertEqual(mint.curve, life.pda(b"bonding-curve", bytes(mint.mint)))
        self.assertEqual(mint.sharing, life.pda(b"sharing-config", bytes(mint.mint), program=life.FEES))

    def test_negative_controls_cross_real_comparator(self):
        receipt = {field: None for field in life.STRICT_FIELDS}
        receipt.update(step="x", after={}, events=[])
        run = {"initial_state_hash": "same", "receipts": [receipt]}
        report = {"cases": [{"original": copy.deepcopy(run), "candidate": copy.deepcopy(run)}]}
        self.assertEqual(life.negative_control(report), {"error": True, "after": True, "events": True})

    def test_missing_receipt_is_a_mismatch(self):
        left = {"initial_state_hash": "same", "receipts": [{}]}
        right = {"initial_state_hash": "same", "receipts": []}
        self.assertIn("receipt_count", life.compare_runs(left, right)[0])


if __name__ == "__main__":
    unittest.main()
