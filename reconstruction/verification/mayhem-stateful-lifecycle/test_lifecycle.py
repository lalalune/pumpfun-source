#!/usr/bin/env python3
from __future__ import annotations

import copy
import base64
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

from lifecycle import run_image  # noqa: E402
from producer import ORIGINAL, canonical_line, produce, sha256_file  # noqa: E402
from verify import verify  # noqa: E402
import producer
from solders.compute_budget import set_compute_unit_limit
from solders.transaction import Transaction


class StatefulLifecycleTests(unittest.TestCase):
    def test_captured_original_has_real_success_failure_and_persistence(self):
        rows = run_image(ORIGINAL)
        self.assertEqual(len(rows), 10)
        self.assertEqual(sum(row["error"] is None for row in rows), 7)
        self.assertEqual(sum(row["error"] is not None for row in rows), 3)
        self.assertEqual(rows[0]["after"], rows[1]["before"])
        self.assertEqual(rows[1]["after"], rows[2]["before"])
        self.assertIn("InstructionErrorCustom(6000)", rows[4]["error"])
        self.assertIn("InstructionErrorCustom(2001)", rows[5]["error"])
        self.assertEqual(rows[8]["before"], rows[7]["after"])

    def test_original_control_verifies_and_replays_byte_identically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            produce(ORIGINAL, first, original_control=True)
            produce(ORIGINAL, second, original_control=True)
            self.assertEqual((first / "receipts.jsonl").read_bytes(), (second / "receipts.jsonl").read_bytes())
            self.assertEqual((first / "report.json").read_bytes(), (second / "report.json").read_bytes())
            result = verify(first / "report.json", ORIGINAL)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["equal_observed_behavior"], 10)
            self.assertTrue(all(row["detected"] for row in result["negative_controls"]))

    def test_semantic_tamper_fails_after_receipt_hash_is_resealed(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "control"
            produce(ORIGINAL, output, original_control=True)
            report_path = output / "report.json"
            report = json.loads(report_path.read_text())
            receipt_path = output / report["receipt_file"]
            rows = [json.loads(line) for line in receipt_path.read_text().splitlines()]
            changed = copy.deepcopy(rows)
            receipt = changed[0]["candidate"]
            key = receipt["account_roles"]["fee_recipient"]
            receipt["after"][key]["lamports"] += 1
            receipt_path.write_text("".join(canonical_line(row) for row in changed), encoding="utf-8", newline="\n")
            report["receipt_sha256"] = sha256_file(receipt_path)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            with self.assertRaisesRegex(ValueError, "SOL conservation"):
                verify(report_path, ORIGINAL)

    def test_producer_summary_is_not_an_acceptance_oracle(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "control"
            produce(ORIGINAL, output, original_control=True)
            report_path = output / "report.json"
            report = json.loads(report_path.read_text())
            report["observed_case_count"] = 999999
            report["observed_signed_transactions"] = 0
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
            result = verify(report_path, ORIGINAL)
            self.assertEqual(result["case_count"], 10)
            self.assertEqual(result["signed_transaction_count"], 20)
            self.assertFalse(result["producer_summary_fields_trusted"])

    def test_unqualified_candidate_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            candidate.write_bytes(b"not a qualified Mayhem image")
            with self.assertRaisesRegex(ValueError, "candidate hash"):
                produce(candidate, root / "output")


class ReceiptAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.control = Path(cls.temporary.name) / "control"
        produce(ORIGINAL, cls.control, original_control=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def rejected(self, mutate, message):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "control"
            shutil.copytree(self.control, output)
            report_path = output / "report.json"
            report = json.loads(report_path.read_text())
            receipt_path = output / "receipts.jsonl"
            rows = [json.loads(line) for line in receipt_path.read_text().splitlines()]
            mutate(report, rows)
            receipt_path.write_text("".join(canonical_line(row) for row in rows))
            report["receipt_sha256"] = sha256_file(receipt_path)
            report_path.write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, message):
                verify(report_path, ORIGINAL)

    def test_signed_unrelated_transaction_cannot_replace_planned_trade(self):
        def mutate(report, rows):
            for side in ("original", "candidate"):
                receipt = rows[0][side]
                tx = Transaction.from_bytes(base64.b64decode(receipt["transaction_base64"]))
                unrelated = Transaction.new_signed_with_payer(
                    [set_compute_unit_limit(1_400_000)], producer.lifecycle.PAYER.pubkey(),
                    [producer.lifecycle.PAYER], tx.message.recent_blockhash)
                receipt.update(transaction_base64=base64.b64encode(bytes(unrelated)).decode(),
                               transaction_sha256=hashlib.sha256(bytes(unrelated)).hexdigest(),
                               signatures=[str(value) for value in unrelated.signatures],
                               signature_verification=unrelated.verify_with_results())
        self.rejected(mutate, "signed instruction plan")

    def test_signature_claims_require_exact_booleans_and_vectors(self):
        def integer_flags(report, rows):
            for side in ("original", "candidate"):
                rows[0][side]["signature_verification"] = [1, 1]
        self.rejected(integer_flags, "producer signature field")
        self.rejected(lambda report, rows: rows[0]["candidate"].update(signatures=[]), "signature vector")

    def test_complete_inputs_mode_plan_and_fixture_are_required(self):
        def empty_inputs(report, rows):
            report.update(input_sha256={}, mayhem_source_files=0,
                          mayhem_source_tree_sha256=hashlib.sha256(b"").hexdigest())
        self.rejected(empty_inputs, "complete current input inventory")
        self.rejected(lambda report, rows: report.update(mode="invented"), "report mode")
        self.rejected(lambda report, rows: report.update(plan=[]), "report plan")
        self.rejected(lambda report, rows: report.update(fixture_classification="initializer_executed"), "fixture classification")

    def test_snapshot_membership_roles_and_metadata_are_required(self):
        intruder = str(producer.lifecycle.INTRUDER.pubkey())
        def missing_key(report, rows):
            for row in rows:
                for side in ("original", "candidate"):
                    for phase in ("before", "after"):
                        del row[side][phase][intruder]
        self.rejected(missing_key, "snapshot membership")
        def bad_role(report, rows):
            rows[0]["original"]["account_roles"]["intruder"] = str(producer.lifecycle.PAYER.pubkey())
        self.rejected(bad_role, "canonical account roles")
        def bad_metadata(report, rows):
            for side in ("original", "candidate"):
                rows[0][side]["after"][intruder]["data_bytes"] += 1
        self.rejected(bad_metadata, "snapshot data metadata")
        def missing_executable(report, rows):
            for row in rows:
                for side in ("original", "candidate"):
                    for phase in ("before", "after"):
                        row[side][phase][str(producer.lifecycle.PUMP)] = None
        self.rejected(missing_executable, "executable snapshot metadata")

    def test_exact_failure_instruction_and_json_are_required(self):
        def wrong_instruction(report, rows):
            for side in ("original", "candidate"):
                rows[4][side]["error"] = "TransactionErrorInstructionError((2, Tagged(InstructionErrorCustom(6000))))"
        self.rejected(wrong_instruction, "exact error code/instruction index")
        from verify import strict_loads
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            strict_loads('{"schema":1,"schema":1}')
        with self.assertRaisesRegex(ValueError, "nonfinite JSON number"):
            strict_loads('{"value":NaN}')

    def test_each_side_requires_continuity_and_constructor_prestate(self):
        intruder = str(producer.lifecycle.INTRUDER.pubkey())
        def disconnected(report, rows):
            for side in ("original", "candidate"):
                rows[1][side]["before"][intruder]["lamports"] += 1
        self.rejected(disconnected, "state continuity/constructor prestate")
        def false_start(report, rows):
            for row in rows:
                for side in ("original", "candidate"):
                    for phase in ("before", "after"):
                        row[side][phase][intruder]["lamports"] += 1
        self.rejected(false_start, "state continuity/constructor prestate")

    def test_changed_inputs_or_image_during_production_are_rejected(self):
        fixture = HERE / "fixture.json"
        original_bytes = fixture.read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            def alter_input(image):
                fixture.write_bytes(original_bytes + b"\n")
                return []
            try:
                with mock.patch.object(producer, "run_image", alter_input), self.assertRaisesRegex(ValueError, "input inventory or bytes changed"):
                    producer.produce(ORIGINAL, Path(temporary) / "inputs", original_control=True)
            finally:
                fixture.write_bytes(original_bytes)
            candidate = Path(temporary) / "copy.so"
            candidate.write_bytes(ORIGINAL.read_bytes())
            def alter_image(image):
                if image.resolve() == candidate.resolve():
                    candidate.write_bytes(b"altered executable")
                return []
            with mock.patch.object(producer, "run_image", alter_image), self.assertRaisesRegex(ValueError, "candidate image changed"):
                producer.produce(candidate, Path(temporary) / "image", original_control=True)

    def test_source_only_fixture_ignores_timestamp_valid_bytecode(self):
        import importlib._bootstrap_external as bootstrap
        fixture = ROOT / "scripts/pump_trade_fixture.py"
        cache = Path(importlib.util.cache_from_source(str(fixture)))
        existing = cache.read_bytes() if cache.exists() else None
        cache.parent.mkdir(exist_ok=True)
        stat = fixture.stat()
        code = compile("raise RuntimeError('unadmitted bytecode executed')", str(fixture), "exec")
        cache.write_bytes(bootstrap._code_to_timestamp_pyc(code, int(stat.st_mtime), stat.st_size))
        try:
            ordinary = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, sys.argv[1]); import pump_trade_fixture", str(fixture.parent)], capture_output=True, text=True)
            self.assertNotEqual(ordinary.returncode, 0)
            self.assertIn("unadmitted bytecode executed", ordinary.stderr)
            admitted = subprocess.run([sys.executable, str(HERE / "producer.py"), "--help"], capture_output=True, text=True)
            self.assertEqual(admitted.returncode, 0, admitted.stderr)
        finally:
            if existing is None:
                cache.unlink(missing_ok=True)
            else:
                cache.write_bytes(existing)

    def test_outputs_stay_outside_repository_and_optimized_python_fails(self):
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            producer.produce(ORIGINAL, HERE / "forbidden-output", original_control=True)
        self.assertFalse((HERE / "forbidden-output").exists())
        for entry in ("producer.py", "verify.py"):
            completed = subprocess.run([sys.executable, "-O", str(HERE / entry), "--help"], capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("Normal Python is required", completed.stderr)


if __name__ == "__main__":
    unittest.main()
