#!/usr/bin/env python3
import base64
import copy
import gzip
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus as P  # noqa: E402
C = P.source_module("campaign", HERE / "campaign.py", imports={"corpus": P})
E = C.E
V = P.source_module("verify_report", HERE / "verify_report.py", imports={"corpus": P, "executor": E})


class ReportVerificationTests(unittest.TestCase):
    original = E.L.CAPTURED["pump_original"]

    @classmethod
    def setUpClass(cls):
        cls._temporary = tempfile.TemporaryDirectory()
        cls._base = Path(cls._temporary.name) / "base"
        C.run_campaign(original=cls.original, candidate=cls.original,
                       output=cls._base, seed=20261101, count=1)

    @classmethod
    def tearDownClass(cls):
        cls._temporary.cleanup()

    def _campaign(self, root):
        output = Path(root) / "campaign"
        shutil.copytree(self._base, output)
        for name in ("attempt.json", "complete.json"):
            path = output / name
            document = json.loads(path.read_bytes())
            document["output_name"] = output.name
            path.write_bytes(P.canonical_json(document))
        return output

    def _reseal(self, output, summary):
        (output / "artifacts.json").write_bytes(P.canonical_json(P.artifact_manifest(output)))
        summary["artifact_manifest_sha256"] = P.file_sha(output / "artifacts.json")
        unsigned = dict(summary)
        unsigned.pop("summary_sha256", None)
        summary["summary_sha256"] = hashlib.sha256(P.canonical_json(unsigned)).hexdigest()
        (output / "summary.json").write_bytes(P.canonical_json(summary))
        complete = json.loads((output / "complete.json").read_bytes())
        complete.update(summary_sha256=summary["summary_sha256"],
                        artifact_manifest_sha256=summary["artifact_manifest_sha256"],
                        classification_counts=summary["classification_counts"])
        for path, document in ((output / "attempt.json", json.loads((output / "attempt.json").read_bytes())),
                               (output / "complete.json", complete)):
            for key in ("seed", "start_index"):
                if key in document:
                    document[key] = summary[key]
            if "count" in document:
                document["count"] = summary["case_count"]
            if "case_manifest_sha256" in document:
                document["case_manifest_sha256"] = summary["case_manifest_sha256"]
            path.write_bytes(P.canonical_json(document))

    def _mutate_execution(self, output, mutate):
        summary = json.loads((output / "summary.json").read_bytes())
        path = next((output / "receipts").glob("*.gz"))
        execution = json.loads(gzip.decompress(path.read_bytes()))
        mutate(execution)
        path.write_bytes(P.compressed_json(execution))
        summary["cases"][0] = V._summary_row(execution)
        self._reseal(output, summary)
        return summary

    def test_complete_report_verifies_and_reexecutes(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            result = V.verify_campaign(output, self.original, self.original, reexecute=True)
            self.assertTrue(result["valid"], result)
            self.assertTrue(result["runtime_verified"], result)
            self.assertEqual(result["verified_receipt_count"], 1)
            self.assertEqual(result["reexecuted_case_count"], 1)

    def test_corrupted_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            receipt = next((output / "receipts").glob("*.gz"))
            raw = bytearray(receipt.read_bytes())
            raw[len(raw) // 2] ^= 1
            receipt.write_bytes(raw)
            result = V.verify_campaign(output, self.original, self.original)
            self.assertFalse(result["valid"])

    def test_tampered_executable_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            candidate = Path(temp) / "candidate.so"
            shutil.copyfile(self.original, candidate)
            candidate.write_bytes(candidate.read_bytes() + b"tamper")
            result = V.verify_campaign(output, self.original, candidate)
            self.assertFalse(result["valid"])
            self.assertIn("input-hash:pump_candidate", result["failures"])

    def test_fully_resealed_signed_unrelated_message_is_rejected(self):
        from solders.instruction import Instruction
        from solders.hash import Hash
        from solders.transaction import Transaction
        from solders.compute_budget import set_compute_unit_limit
        def mutate(result):
            for side in ("original", "candidate"):
                row = result[side]["receipts"][0]
                instruction = Instruction(E.L.PUMP, b"unrelated", [])
                tx = Transaction.new_signed_with_payer(
                    [set_compute_unit_limit(1_400_000), instruction], E.L.PAYER.pubkey(),
                    [E.L.PAYER], Hash.from_string(row["recent_blockhash"]))
                row.update(transaction_base64=base64.b64encode(bytes(tx)).decode(),
                           signature=str(tx.signatures[0]), signature_verification=list(tx.verify_with_results()),
                           message_sha256=E.sha(bytes(tx.message)), instruction_accounts=[],
                           instruction_data_base64=base64.b64encode(bytes(instruction.data)).decode())
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            self._mutate_execution(output, mutate)
            result = V.verify_campaign(output, self.original, self.original)
            self.assertFalse(result["valid"], result)
            self.assertTrue(any("transaction-integrity" in f for f in result["failures"]), result)

    def test_fully_resealed_integer_flags_and_omitted_state_are_rejected(self):
        def flags(result):
            for side in ("original", "candidate"):
                for row in result[side]["receipts"]:
                    row["signature_verification"] = [1] * len(row["signature_verification"])
        def omitted(result):
            for side in ("original", "candidate"):
                for row in result[side]["receipts"]:
                    for stage in ("before", "after"):
                        row[stage].pop(str(E.L.GLOBAL))
                        row[stage + "_hash"] = E.L.canonical_hash(row[stage])
                result[side]["initial_state_hash"] = result[side]["receipts"][0]["before_hash"]
        for mutate in (flags, omitted):
            with self.subTest(mutate=mutate.__name__), tempfile.TemporaryDirectory() as temp:
                output = self._campaign(temp)
                self._mutate_execution(output, mutate)
                self.assertFalse(V.verify_campaign(output, self.original, self.original)["valid"])

    def test_fully_resealed_unsupported_exclusion_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            path = next((output / "receipts").glob("*.gz"))
            old = json.loads(gzip.decompress(path.read_bytes()))
            forged = {"schema": E.SCHEMA, "case_id": old["case_id"], "case": old["case"],
                      "classification": "unsupported_fixture", "reason": "invented exclusion"}
            path.write_bytes(P.compressed_json(forged))
            summary = json.loads((output / "summary.json").read_bytes())
            summary["cases"] = [V._summary_row(forged)]
            summary["classification_counts"] = {name: int(name == "unsupported_fixture")
                                                 for name in summary["classification_counts"]}
            summary.update(transaction_count_per_image=0, executed_case_count=0,
                           original_successful_case_count=0, runtime_verified=False,
                           negative_controls={"available": False})
            self._reseal(output, summary)
            result = V.verify_campaign(output, self.original, self.original)
            self.assertFalse(result["valid"], result)
            self.assertTrue(any("unsupported-fixture-not-reproduced" in f for f in result["failures"]), result)

    def test_zero_case_resealed_campaign_and_typed_count_are_rejected(self):
        for zero in (True, False):
            with self.subTest(zero=zero), tempfile.TemporaryDirectory() as temp:
                output = self._campaign(temp)
                summary = json.loads((output / "summary.json").read_bytes())
                summary["case_count"] = 0 if zero else True
                if zero:
                    shutil.rmtree(output / "receipts")
                    (output / "cases.json").write_bytes(P.canonical_json([]))
                    summary.update(cases=[], case_manifest_sha256=hashlib.sha256(V.C.canonical([])).hexdigest(),
                                   classification_counts={k: 0 for k in summary["classification_counts"]},
                                   transaction_count_per_image=0, executed_case_count=0,
                                   original_successful_case_count=0, runtime_verified=False,
                                   negative_controls={"available": False})
                self._reseal(output, summary)
                result = V.verify_campaign(output, self.original, self.original, reexecute=True)
                self.assertFalse(result["valid"], result)
                self.assertEqual(result["reexecuted_case_count"], 0)

    def test_resealed_tranche_and_summary_aggregate_changes_are_rejected(self):
        for field in ("seed", "transaction_count_per_image", "original_successful_case_count"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                output = self._campaign(temp)
                summary = json.loads((output / "summary.json").read_bytes())
                summary[field] += 1
                self._reseal(output, summary)
                self.assertFalse(V.verify_campaign(output, self.original, self.original)["valid"])

    def test_report_mutation_during_admission_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            original = V.E.validate_result
            def changing(*args, **kwargs):
                result = original(*args, **kwargs)
                path = output / "summary.json"
                path.write_bytes(path.read_bytes() + b" ")
                return result
            with mock.patch.object(V.E, "validate_result", side_effect=changing):
                result = V.verify_campaign(output, self.original, self.original)
            self.assertFalse(result["valid"], result)
            self.assertIn("report-changed-during-verification", result["failures"])

    def test_image_mutation_during_receipt_admission_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            candidate = Path(temp) / "candidate.so"
            shutil.copyfile(self.original, candidate)
            original = V.E.validate_result
            def changing(*args, **kwargs):
                result = original(*args, **kwargs)
                candidate.write_bytes(candidate.read_bytes() + b"mutated")
                return result
            with mock.patch.object(V.E, "validate_result", side_effect=changing):
                result = V.verify_campaign(output, self.original, candidate)
            self.assertFalse(result["valid"], result)
            self.assertIn("inputs-changed-during-verification", result["failures"])

    def test_compact_mode_requires_explicit_provenance_only(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            summary = json.loads((output / "summary.json").read_bytes())
            shutil.rmtree(output / "receipts")
            (output / "progress").mkdir()
            case_id = summary["cases"][0]["case_id"]
            (output / "progress" / ("0000-" + case_id + ".json")).write_bytes(P.canonical_json(summary["cases"][0]))
            summary["detailed_receipts"] = False
            self._reseal(output, summary)
            self.assertFalse(V.verify_campaign(output, self.original, self.original)["valid"])
            admitted = V.verify_campaign(output, self.original, self.original, provenance_only=True)
            self.assertTrue(admitted["valid"], admitted)
            self.assertFalse(admitted["runtime_verified"])
            self.assertEqual(admitted["verification_scope"], "provenance-only")

    def test_fully_resealed_listed_extra_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = self._campaign(temp)
            summary = json.loads((output / "summary.json").read_bytes())
            (output / "extra-listed.json").write_text("{}")
            self._reseal(output, summary)
            result = V.verify_campaign(output, self.original, self.original)
            self.assertFalse(result["valid"], result)
            self.assertIn("artifact-membership-for-plan", result["failures"])

    def test_links_unlisted_members_and_duplicate_json_are_rejected(self):
        for kind in ("link", "extra", "duplicate"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                output = self._campaign(temp)
                if kind == "link":
                    path = output / "cases.json"
                    outside = Path(temp) / "cases.json"
                    path.replace(outside)
                    path.symlink_to(outside)
                elif kind == "extra":
                    (output / "unlisted.json").write_text("{}")
                else:
                    path = output / "summary.json"
                    raw = path.read_text()
                    path.write_text(raw.replace("{", '{"schema":"duplicate",', 1))
                self.assertFalse(V.verify_campaign(output, self.original, self.original)["valid"])


if __name__ == "__main__":
    unittest.main()
