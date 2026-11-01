import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("fuzz_corpus_for_selection", HERE / "corpus.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
C = P.source_module("selection_case_model", HERE / "case_model.py")
E = P.source_module("selection_executor", HERE / "executor.py",
                    imports={"case_model": C, "corpus": P})
B = P.source_module("selection_under_test", HERE / "behavior.py",
                    imports={"case_model": C, "executor": E})
ORIGINAL = E.L.CAPTURED["pump_original"]


class GuidedSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = C.generate_corpus(20261101, 16)
        cls.observations = [B.observe_case(case, ORIGINAL) for case in cls.cases]

    def test_selection_is_deterministic_and_preserves_seed_identity(self):
        first = B.select_corpus(self.cases, self.observations, 12)
        second = B.select_corpus(copy.deepcopy(self.cases),
                                 copy.deepcopy(self.observations), 12)
        self.assertEqual(first, second)
        self.assertEqual(first["selection_sha256"], B.digest({
            key: value for key, value in first.items() if key != "selection_sha256"
        }))
        by_id = {case["case_id"]: case for case in self.cases}
        for row in first["selected"]:
            case = by_id[row["case_id"]]
            self.assertEqual(case, C.generate_case(case["root_seed"], case["case_index"]))

    def test_same_budget_guidance_retains_more_observed_classes(self):
        selection = B.select_corpus(self.cases, self.observations, 12)
        self.assertEqual(selection["retained_count"], 12)
        self.assertGreater(selection["selected_behavior_class_count"],
                           selection["unguided_behavior_class_count"])
        self.assertEqual(selection["selected_behavior_class_count"], 12)
        self.assertEqual(selection["unguided_behavior_class_count"], 11)

    def test_cases_sharing_one_outcome_group_are_represented_once_first(self):
        selection = B.select_corpus(self.cases, self.observations, 12)
        representatives = [row for row in selection["selected"]
                           if "bounded-class-member" not in row["selection_reasons"]]
        fingerprints = [row["fingerprint_sha256"] for row in representatives]
        self.assertEqual(len(fingerprints), len(set(fingerprints)))

    def test_success_failure_and_boundary_anchors_are_retained(self):
        selection = B.select_corpus(self.cases, self.observations, 12)
        reasons = {reason for row in selection["selected"]
                   for reason in row["selection_reasons"]}
        self.assertIn("underrepresented-success", reasons)
        self.assertIn("known-failure", reasons)
        self.assertIn("boundary", reasons)
        self.assertGreaterEqual(selection["selected_success_count"], 1)

    def test_unsupported_cases_never_increase_behavior_counts(self):
        selection = B.select_corpus(self.cases, self.observations, 12)
        unsupported = {row["case_id"] for row in selection["rows"]
                       if row["classification"] == "unsupported_fixture"}
        self.assertTrue(unsupported)
        self.assertTrue(unsupported.isdisjoint(row["case_id"] for row in selection["selected"]))
        self.assertEqual(selection["eligible_count"] + selection["unsupported_count"]
                         + selection["infrastructure_failure_count"],
                         selection["deduplicated_pool_count"])

    def test_exact_duplicate_inputs_are_deduplicated(self):
        cases = [self.cases[0], copy.deepcopy(self.cases[0]), self.cases[1]]
        observations = [self.observations[0], copy.deepcopy(self.observations[0]),
                        self.observations[1]]
        selection = B.select_corpus(cases, observations, 2)
        self.assertEqual(selection["pool_count"], 3)
        self.assertEqual(selection["deduplicated_pool_count"], 2)
        self.assertEqual(len({row["case_id"] for row in selection["selected"]}),
                         len(selection["selected"]))

    def test_limits_and_rank_tampering_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "corpus limit"):
            B.select_corpus(self.cases, self.observations, 0)
        selection = B.select_corpus(self.cases, self.observations, 12)
        changed = copy.deepcopy(selection)
        changed["selected"][0]["rank"] = 2
        self.assertIn("selection-recomputation",
                      B.validate_selection(changed, self.cases, self.observations, 12))


if __name__ == "__main__":
    unittest.main()
