import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("guided_campaign_module", HERE / "guided_campaign.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
ORIGINAL = G.E.L.CAPTURED["pump_original"]
ORIGINAL_SHA = G.E.CANONICAL_ORIGINAL_SHA256


class GuidedCampaignTests(unittest.TestCase):
    def run_campaign(self, output, **changes):
        options = dict(original=ORIGINAL, candidate=ORIGINAL, output=output,
                       seed=20261101, pool_count=8, corpus_limit=4,
                       expected_original_sha256=ORIGINAL_SHA,
                       expected_candidate_sha256=ORIGINAL_SHA,
                       reduce_mismatches=True)
        options.update(changes)
        return G.run_guided_campaign(**options)

    def test_original_control_is_deterministic_and_strict(self):
        with tempfile.TemporaryDirectory() as temp:
            first = self.run_campaign(Path(temp) / "first")
            second = self.run_campaign(Path(temp) / "second")
        for summary in (first, second):
            self.assertEqual(summary["classification_counts"], {
                "equal_observed_behavior": 4, "different_behavior": 0,
                "unsupported_fixture": 0, "infrastructure_failure": 0,
            })
            self.assertTrue(summary["runtime_verified"])
            self.assertTrue(summary["negative_controls"]["all_detected"])
        ignored = {"artifact_manifest_sha256", "summary_sha256"}
        self.assertEqual({k: v for k, v in first.items() if k not in ignored},
                         {k: v for k, v in second.items() if k not in ignored})

    def test_selected_cases_remain_replayable_by_root_seed(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report"
            self.run_campaign(output)
            cases = G.P.read_json(output / "cases.json")
        for case in cases:
            self.assertEqual(case, G.C.generate_case(case["root_seed"], case["case_index"]))

    def test_existing_output_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report"
            self.run_campaign(output)
            before = G.P.report_files_digest(output)
            with self.assertRaises(FileExistsError):
                self.run_campaign(output)
            self.assertEqual(before, G.P.report_files_digest(output))

    def test_invalid_bounds_fail_before_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report"
            with self.assertRaisesRegex(ValueError, "pool count"):
                self.run_campaign(output, pool_count=0)
            self.assertFalse(output.exists())

    def test_callback_cannot_mutate_retained_observation(self):
        def callback(_index, _case, observation):
            observation["classification"] = "unsupported_fixture"
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "report"
            summary = self.run_campaign(output, after_observation=callback)
            retained = G.P.read_json(output / "selection.json")
        self.assertEqual(summary["observation_counts"]["unsupported_fixture"], 0)
        self.assertEqual(retained["unsupported_count"], 0)


if __name__ == "__main__":
    unittest.main()
