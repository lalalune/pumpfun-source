#!/usr/bin/env python3
import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import case_model as C  # noqa: E402
import reducer as R  # noqa: E402


def case(fee=64):
    value = {
        "schema": C.SCHEMA, "generator": C.GENERATOR,
        "root_seed": 8, "case_index": 0, "case_seed": C.derive_case_seed(8, 0),
        "config": {"mints": ["native"], "shared": False, "complete": False,
                   "holder_initial": False, "native_vault_lamports": 890_880},
        "initial_mutations": [
            {"target": "global", "action": "lamports", "value": 1_000_000},
            {"target": "curve", "action": "set_byte", "offset": 48, "value": 1},
        ],
        "steps": [
            {"name": "mismatch", "op": "admin_cto", "new": 2, "holder": False,
             "fee": fee, "readonly": [9]},
            {"name": "irrelevant", "op": "admin_cto", "new": 3},
        ],
    }
    value["case_id"] = C.case_identity(value)
    return C.validate_case(value)


def receipt(step, outcome, after):
    return {"step": step, "outcome": outcome, "after": after}


def evaluator(value):
    fee = next((step.get("fee", 0) for step in value["steps"] if step["name"] == "mismatch"), 0)
    essential = any(row.get("target") == "curve" for row in value["initial_mutations"])
    left = [receipt(step["name"], "ok", {"value": 0}) for step in value["steps"]]
    right = copy.deepcopy(left)
    mismatches, comparisons = [], []
    for index, step in enumerate(value["steps"]):
        fields = []
        if step["name"] == "mismatch" and fee >= 8 and essential:
            right[index]["after"] = {"value": 1}
            fields = ["after"]
            mismatches.append("mismatch:after")
        comparisons.append({"step": step["name"], "mismatch_fields": fields})
    return {"classification": "different_behavior" if mismatches else "equal_observed_behavior",
            "original": {"receipts": left}, "candidate": {"receipts": right},
            "comparison": comparisons, "mismatch_fields": mismatches}


class ReducerTests(unittest.TestCase):
    def test_reducer_removes_irrelevance_and_finds_numeric_boundary(self):
        reduced = R.reduce_case(case(), evaluator)
        final = reduced["case"]
        self.assertEqual([step["name"] for step in final["steps"]], ["mismatch"])
        self.assertEqual(final["steps"][0]["fee"], 8)
        self.assertEqual(final["initial_mutations"],
                         [{"target": "curve", "action": "set_byte", "offset": 0, "value": 0}])
        self.assertTrue(reduced["minimality"]["demonstrated"])
        self.assertLess(R.complexity_tuple(final), R.complexity_tuple(case()))

    def test_incorrect_reduction_is_reexecuted_and_rejected(self):
        reduced = R.reduce_case(case(), evaluator)
        self.assertTrue(any(not row["preserved_property"] for row in reduced["attempts"]))
        self.assertTrue(any(row.get("target") == "curve"
                            for row in reduced["case"]["initial_mutations"]))

    def test_reduction_is_stable(self):
        left = R.reduce_case(case(), evaluator)
        right = R.reduce_case(case(), evaluator)
        self.assertEqual(left["reduced_case_id"], right["reduced_case_id"])
        self.assertEqual(left["accepted_reductions"], right["accepted_reductions"])

    def test_budget_exhaustion_never_claims_minimality(self):
        reduced = R.reduce_case(case(), evaluator, max_trials=1)
        self.assertFalse(reduced["minimality"]["demonstrated"])
        self.assertTrue(reduced["minimality"]["unchecked_case_ids"])

    def test_non_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "does not demonstrate"):
            R.reduce_case(case(fee=1), evaluator)

    def test_retained_witness_and_explicit_neighborhood_replay_verify(self):
        original = case()
        reduced = R.reduce_case(original, evaluator)
        self.assertEqual(R.validate_reduction(reduced, original, evaluator(original)), [])
        self.assertEqual(R.validate_reduction(reduced, original, evaluator(original), evaluate=evaluator), [])

    def test_false_execution_count_and_changed_witness_are_rejected(self):
        original = case()
        reduced = R.reduce_case(original, evaluator)
        bad = copy.deepcopy(reduced)
        bad["executions"] = True
        self.assertIn("reduction-execution-budget", R.validate_reduction(bad, original, evaluator(original)))
        bad = copy.deepcopy(reduced)
        bad["result"] = evaluator(case(fee=1))
        self.assertIn("reduction-mismatch-property", R.validate_reduction(bad, original, evaluator(original)))

    def test_unavailable_neighbors_do_not_establish_minimality(self):
        original = case()
        def unavailable(value):
            return evaluator(value) if value["case_id"] == original["case_id"] else {
                "classification": "unsupported_fixture"}
        reduced = R.reduce_case(original, unavailable)
        self.assertFalse(reduced["minimality"]["demonstrated"])
        self.assertTrue(reduced["minimality"]["unchecked_case_ids"])

    def test_empty_difference_claim_is_not_a_counterexample(self):
        original = case()
        empty = {"classification": "different_behavior", "mismatch_fields": [],
                 "comparison": [], "original": {"receipts": []}, "candidate": {"receipts": []}}
        self.assertIsNone(R.mismatch_property(empty))
        with self.assertRaisesRegex(ValueError, "does not demonstrate"):
            R.reduce_case(original, lambda _: empty)


if __name__ == "__main__":
    unittest.main()
