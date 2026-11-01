import copy
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
import importlib.util

spec = importlib.util.spec_from_file_location("fuzz_corpus_for_behavior", HERE / "corpus.py")
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
C = P.source_module("behavior_case_model", HERE / "case_model.py")
E = P.source_module("behavior_executor", HERE / "executor.py", imports={"case_model": C, "corpus": P})
B = P.source_module("behavior_under_test", HERE / "behavior.py",
                    imports={"case_model": C, "executor": E})

ORIGINAL = E.L.CAPTURED["pump_original"]


class BehaviorFingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = C.generate_case(20261101, 2)
        cls.observation = B.observe_case(cls.case, ORIGINAL)
        if cls.observation["classification"] != "observed_behavior":
            raise AssertionError(cls.observation)

    def test_encoding_is_stable_and_versioned(self):
        first = B.behavior_fingerprint(self.case, self.observation["original"])
        second = B.behavior_fingerprint(copy.deepcopy(self.case),
                                        copy.deepcopy(self.observation["original"]))
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], B.FINGERPRINT_SCHEMA)
        self.assertEqual(first["payload"]["schema"], B.FINGERPRINT_SCHEMA)
        self.assertEqual(first["sha256"], B.digest(first["payload"]))

    def test_observable_outcome_change_produces_new_fingerprint(self):
        changed = copy.deepcopy(self.observation["original"])
        changed["receipts"][0]["outcome"] = "error:negative-control"
        # Fingerprinting itself is intentionally receipt-admitted.
        with self.assertRaisesRegex(ValueError, "invalid original run"):
            B.behavior_fingerprint(self.case, changed)

    def test_observation_admission_recomputes_fingerprint(self):
        self.assertEqual(B.validate_observation(self.observation, self.case), [])
        changed = copy.deepcopy(self.observation)
        changed["fingerprint"]["sha256"] = "0" * 64
        self.assertIn("fingerprint", B.validate_observation(changed, self.case))

    def test_fingerprint_records_observed_categories_not_code_coverage(self):
        payload = self.observation["fingerprint"]["payload"]
        self.assertNotIn("coverage", payload)
        self.assertTrue(payload["steps"])
        for step in payload["steps"]:
            self.assertIn(step["stage"], ("success", "failed_before_cpi", "failed_after_cpi"))
            self.assertIsInstance(step["state_transitions"], list)
            self.assertIsInstance(step["token_program_path"], list)

    def test_boundary_detection_excludes_boolean_integer_aliases(self):
        case = copy.deepcopy(self.case)
        case["config"]["holder_initial"] = True
        self.assertEqual(B.is_boundary_case(case), B.is_boundary_case(self.case))


if __name__ == "__main__":
    unittest.main()
