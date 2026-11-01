import copy
import gzip
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

producer_spec = importlib.util.spec_from_file_location("guided_producer_for_verify", HERE / "guided_campaign.py")
G = importlib.util.module_from_spec(producer_spec)
producer_spec.loader.exec_module(G)
verify_spec = importlib.util.spec_from_file_location("guided_verifier_under_test", HERE / "verify_guided.py")
V = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(V)
ORIGINAL = G.E.L.CAPTURED["pump_original"]
ORIGINAL_SHA = G.E.CANONICAL_ORIGINAL_SHA256


class GuidedVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.report = Path(cls.temp.name) / "report"
        G.run_guided_campaign(
            original=ORIGINAL, candidate=ORIGINAL, output=cls.report,
            seed=20261101, pool_count=8, corpus_limit=4,
            expected_original_sha256=ORIGINAL_SHA,
            expected_candidate_sha256=ORIGINAL_SHA,
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def copy_report(self):
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "report"
        shutil.copytree(self.report, target)
        self.addCleanup(temp.cleanup)
        return target

    @staticmethod
    def read_gzip(path):
        return json.loads(gzip.decompress(path.read_bytes()))

    @staticmethod
    def write_gzip(path, value):
        path.write_bytes(G.P.compressed_json(value))

    @staticmethod
    def reseal(report):
        # Recompute every producer-controlled integrity field so semantic
        # verifier failures cannot be dismissed as a stale outer hash.
        (report / "artifacts.json").write_bytes(G.P.canonical_json(G.P.artifact_manifest(report)))
        artifact_sha = G.P.file_sha(report / "artifacts.json")
        summary = G.P.read_json(report / "summary.json")
        summary["artifact_manifest_sha256"] = artifact_sha
        summary.pop("summary_sha256", None)
        summary["summary_sha256"] = G.hashlib.sha256(G.P.canonical_json(summary)).hexdigest()
        (report / "summary.json").write_bytes(G.P.canonical_json(summary))
        complete = G.P.read_json(report / "complete.json")
        complete["artifact_manifest_sha256"] = artifact_sha
        complete["summary_sha256"] = summary["summary_sha256"]
        complete["classification_counts"] = summary["classification_counts"]
        (report / "complete.json").write_bytes(G.P.canonical_json(complete))

    def verify(self, report, **options):
        return V.verify_guided(report, ORIGINAL, ORIGINAL, **options)

    def test_complete_report_verifies_and_reexecutes(self):
        result = self.verify(self.report, reexecute=True)
        self.assertTrue(result["valid"], result)
        self.assertTrue(result["runtime_verified"])
        self.assertEqual(result["verified_observation_count"], 8)
        self.assertEqual(result["verified_receipt_count"], 4)
        self.assertEqual(result["reexecuted_observation_count"], 8)
        self.assertEqual(result["reexecuted_case_count"], 4)

    def test_forged_novelty_is_detected_after_reseal(self):
        report = self.copy_report()
        path = next((report / "observations").glob("*.json.gz"))
        value = self.read_gzip(path)
        value["fingerprint"]["sha256"] = "0" * 64
        self.write_gzip(path, value)
        self.reseal(report)
        result = self.verify(report)
        self.assertFalse(result["valid"])
        self.assertTrue(any("fingerprint" in row for row in result["failures"]), result)

    def test_corrupted_outcome_and_event_are_detected(self):
        for field in ("outcome", "events"):
            report = self.copy_report()
            path = next((report / "observations").glob("*.json.gz"))
            value = self.read_gzip(path)
            receipt = value["original"]["receipts"][0]
            if field == "outcome":
                receipt[field] = "error:forged"
            else:
                receipt[field].append("Zm9yZ2Vk")
            self.write_gzip(path, value)
            self.reseal(report)
            self.assertFalse(self.verify(report)["valid"], field)

    def test_omitted_case_and_duplicate_id_are_detected(self):
        for mutation in ("omit", "duplicate"):
            report = self.copy_report()
            pool = G.P.read_json(report / "pool.json")
            if mutation == "omit":
                pool.pop()
            else:
                pool[1] = copy.deepcopy(pool[0])
            (report / "pool.json").write_bytes(G.P.canonical_json(pool))
            self.reseal(report)
            self.assertFalse(self.verify(report)["valid"], mutation)

    def test_altered_selection_rank_is_detected_after_reseal(self):
        report = self.copy_report()
        selection = G.P.read_json(report / "selection.json")
        selection["selected"][0]["rank"] = 99
        (report / "selection.json").write_bytes(G.P.canonical_json(selection))
        self.reseal(report)
        result = self.verify(report)
        self.assertFalse(result["valid"])
        self.assertIn("selection-recomputation", result["failures"])

    def test_false_passing_totals_are_detected(self):
        report = self.copy_report()
        summary = G.P.read_json(report / "summary.json")
        summary["classification_counts"]["equal_observed_behavior"] += 1
        summary["selected_case_count"] += 1
        (report / "summary.json").write_bytes(G.P.canonical_json(summary))
        self.reseal(report)
        result = self.verify(report)
        self.assertFalse(result["valid"])
        self.assertTrue(any(row in result["failures"] for row in
                            ("classification-counts", "selected_case_count")), result)

    def test_signature_corruption_is_detected(self):
        report = self.copy_report()
        path = next((report / "receipts").glob("*.json.gz"))
        value = self.read_gzip(path)
        value["original"]["receipts"][0]["signature"] = "forged"
        self.write_gzip(path, value)
        self.reseal(report)
        result = self.verify(report)
        self.assertFalse(result["valid"])
        self.assertTrue(any("transaction-integrity" in row for row in result["failures"]), result)

    def test_missing_evidence_member_is_detected(self):
        report = self.copy_report()
        path = next((report / "observations").glob("*.json.gz"))
        path.unlink()
        result = self.verify(report)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
