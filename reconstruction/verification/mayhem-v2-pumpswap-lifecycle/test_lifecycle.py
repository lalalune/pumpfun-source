#!/usr/bin/env python3
"""Regression tests for the persistent Mayhem V2/PumpSwap package."""
from __future__ import annotations

import base64
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent


def source(path: Path, name: str) -> dict:
    namespace = {"__file__": str(path), "__name__": name}
    exec(compile(path.read_bytes(), str(path), "exec", dont_inherit=True), namespace)
    return namespace


runtime = source(HERE / "runtime.py", "test_runtime")
producer = source(HERE / "producer.py", "test_producer")
verifier = source(HERE / "verify.py", "test_verifier")

from solders.pubkey import Pubkey  # noqa: E402
from solders.transaction import Transaction  # noqa: E402


class FixtureContractTests(unittest.TestCase):
    def test_plan_is_new_persistent_coverage(self):
        plan = runtime["plan"]()
        self.assertEqual(5, len(plan))
        self.assertEqual(14, sum(len(item["steps"]) for item in plan))
        self.assertEqual({"v2", "pumpswap"}, {item["venue"] for item in plan})
        self.assertTrue(any(len(step["instructions"]) == 2 for lifecycle in plan for step in lifecycle["steps"]))
        self.assertTrue(any(step["expect"] == "failure" for lifecycle in plan for step in lifecycle["steps"]))

    def test_signers_are_real_distinct_curve_keys(self):
        trader, payer = runtime["TRADER"], runtime["PAYER"]
        self.assertNotEqual(trader.pubkey(), payer.pubkey())
        self.assertTrue(trader.pubkey().is_on_curve())
        self.assertTrue(payer.pubkey().is_on_curve())

    def test_canonical_mayhem_pdas(self):
        vm = runtime["V2VM"](producer["ORIGINAL"])
        mayhem = runtime["MAYHEM"]
        self.assertEqual(Pubkey.find_program_address([b"global-params"], mayhem)[0], vm.keys["global_params"])
        self.assertEqual(Pubkey.find_program_address([b"sol-vault"], mayhem)[0], vm.keys["sol_vault"])
        self.assertEqual(Pubkey.find_program_address([b"mayhem-state", bytes(vm.keys["mint"])], mayhem)[0], vm.keys["mayhem_state"])

    def test_v2_serialization_and_token_program_selection(self):
        vm = runtime["V2VM"](producer["ORIGINAL"])
        buy = vm.build_instruction("buy_v2")
        sell = vm.build_instruction("sell_v2")
        self.assertEqual(runtime["selector"]("buy_v2"), bytes(buy.data[:8]))
        self.assertEqual(runtime["selector"]("sell_v2"), bytes(sell.data[:8]))
        self.assertEqual(28, len(buy.data))
        self.assertIn(runtime["TOKEN"] , [meta.pubkey for meta in buy.accounts])
        self.assertIn(runtime["TOKEN_2022"], [meta.pubkey for meta in buy.accounts])
        self.assertTrue(buy.accounts[0].is_signer)
        self.assertFalse(any(meta.is_signer for meta in buy.accounts[1:]))

    def test_pumpswap_serialization_and_program_selection(self):
        vm = runtime["PumpSwapVM"](producer["ORIGINAL"])
        buy = vm.build_instruction("buy_pump_swap")
        sell = vm.build_instruction("sell_pump_swap")
        self.assertEqual(runtime["selector"]("buy_pump_swap"), bytes(buy.data[:8]))
        self.assertEqual(runtime["selector"]("sell_pump_swap"), bytes(sell.data[:8]))
        self.assertIn(runtime["AMM"], [meta.pubkey for meta in buy.accounts])
        self.assertGreater(len(buy.accounts), len(sell.accounts))

    def test_independent_vm_construction(self):
        first = runtime["V2VM"](producer["ORIGINAL"])
        second = runtime["V2VM"](producer["ORIGINAL"])
        initial = second.snapshot()
        lifecycle = runtime["plan"]()[0]
        first.execute(lifecycle["name"], lifecycle["steps"][0])
        self.assertEqual(initial, second.snapshot())
        self.assertNotEqual(initial, first.snapshot())


class PersistentExecutionTests(unittest.TestCase):
    def test_v2_state_continuity_and_fresh_blockhashes(self):
        lifecycle = runtime["plan"]()[0]
        vm = runtime["V2VM"](producer["ORIGINAL"])
        rows = [vm.execute(lifecycle["name"], step) for step in lifecycle["steps"]]
        self.assertTrue(all(row["error"] is None for row in rows))
        self.assertEqual(rows[0]["after"], rows[1]["before"])
        self.assertEqual(rows[1]["after"], rows[2]["before"])
        self.assertEqual(3, len({row["recent_blockhash"] for row in rows}))
        self.assertTrue(all(row["signature_verification"] == [True, True] for row in rows))

    def test_pumpswap_state_continuity(self):
        lifecycle = next(item for item in runtime["plan"]() if item["name"] == "pumpswap_buy_buy_sell")
        vm = runtime["PumpSwapVM"](producer["ORIGINAL"])
        rows = [vm.execute(lifecycle["name"], step) for step in lifecycle["steps"]]
        self.assertTrue(all(row["error"] is None for row in rows))
        self.assertEqual(rows[0]["after"], rows[1]["before"])
        self.assertEqual(rows[1]["after"], rows[2]["before"])

    def test_failed_slippage_rolls_back_and_retry_succeeds(self):
        lifecycle = next(item for item in runtime["plan"]() if item["name"] == "v2_failure_retry_atomic")
        vm = runtime["V2VM"](producer["ORIGINAL"])
        rows = [vm.execute(lifecycle["name"], step) for step in lifecycle["steps"]]
        failure = rows[1]
        self.assertIn("InstructionErrorCustom(6012)", failure["error"])
        verifier["verify_failed_rollback"](failure)
        self.assertIsNone(rows[2]["error"])
        self.assertEqual(failure["after"], rows[2]["before"])

    def test_atomic_v2_and_pumpswap_transactions_are_genuine(self):
        for lifecycle_name, cls in (
            ("v2_failure_retry_atomic", runtime["V2VM"]),
            ("pumpswap_atomic_buy_sell", runtime["PumpSwapVM"]),
        ):
            lifecycle = next(item for item in runtime["plan"]() if item["name"] == lifecycle_name)
            step = next(item for item in lifecycle["steps"] if len(item["instructions"]) == 2)
            vm = cls(producer["ORIGINAL"])
            if lifecycle_name.startswith("v2_"):
                for prior in lifecycle["steps"]:
                    if prior is step:
                        break
                    vm.execute(lifecycle["name"], prior)
            row = vm.execute(lifecycle["name"], step)
            tx = Transaction.from_bytes(base64.b64decode(row["transaction_base64"]))
            self.assertIsNone(row["error"])
            self.assertEqual(3, len(tx.message.instructions))
            self.assertEqual([True, True], list(tx.verify_with_results()))

    def test_numeric_boundary_has_exact_captured_error(self):
        vm = runtime["PumpSwapVM"](producer["ORIGINAL"])
        lifecycle = {"name": "boundary"}
        step = {"name": "zero_reference", "instructions": ["buy_pump_swap_invalid_reference"], "expect": "failure"}
        receipt = vm.execute(lifecycle["name"], step)
        self.assertEqual("TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(6012))))", receipt["error"])
        verifier["verify_failed_rollback"](receipt)


class ProducerVerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="mayhem-v2-pumpswap-tests-")
        cls.root = Path(cls.temporary.name)
        cls.output = cls.root / "control"
        producer["produce"](producer["ORIGINAL"], cls.output, True)
        cls.report_path = cls.output / "report.json"

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_original_control_passes_independent_verification(self):
        result = verifier["verify"](self.report_path, producer["ORIGINAL"])
        self.assertEqual("PASS", result["status"])
        self.assertEqual(14, result["equal_observed_behavior"])
        self.assertEqual(0, result["different_behavior"])
        self.assertEqual(12, result["successful_original_transitions"])
        self.assertEqual(2, result["failed_original_transitions"])

    def test_all_ten_negative_controls_are_detected(self):
        result = verifier["verify"](self.report_path, producer["ORIGINAL"])
        self.assertEqual(10, len(result["negative_controls"]))
        self.assertTrue(all(item["detected"] for item in result["negative_controls"]))

    def test_deterministic_replay(self):
        second = self.root / "control-second"
        producer["produce"](producer["ORIGINAL"], second, True)
        self.assertEqual((self.output / "receipts.jsonl").read_bytes(), (second / "receipts.jsonl").read_bytes())
        self.assertEqual((self.output / "report.json").read_bytes(), (second / "report.json").read_bytes())

    def test_existing_output_is_never_overwritten(self):
        existing = self.root / "existing"
        existing.mkdir()
        marker = existing / "marker"
        marker.write_text("preserve")
        with self.assertRaises(FileExistsError):
            producer["produce"](producer["ORIGINAL"], existing, True)
        self.assertEqual("preserve", marker.read_text())

    def test_repository_output_is_refused(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            producer["produce"](producer["ORIGINAL"], HERE / "forbidden-output", True)

    def test_tampered_receipt_file_is_refused(self):
        report = json.loads(self.report_path.read_text())
        changed = self.root / "tampered"
        changed.mkdir()
        (changed / "report.json").write_text(json.dumps(report))
        receipts = (self.output / "receipts.jsonl").read_bytes() + b"\n"
        (changed / "receipts.jsonl").write_bytes(receipts)
        with self.assertRaisesRegex(ValueError, "receipt hash"):
            verifier["verify"](changed / "report.json", producer["ORIGINAL"])

    def test_duplicate_report_key_is_refused(self):
        raw = self.report_path.read_text().replace('"schema":', '"schema":"duplicate","schema":', 1)
        changed = self.root / "duplicate-report.json"
        changed.write_text(raw)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            verifier["verify"](changed, producer["ORIGINAL"])

    def test_changed_declared_inputs_fail_closed(self):
        first = producer["inventory"]()
        changed = dict(first)
        changed["plan.json"] = "0" * 64
        with mock.patch.dict(producer, {"inventory": mock.Mock(side_effect=[first, changed])}):
            output = self.root / "input-race"
            with self.assertRaisesRegex(ValueError, "input changed"):
                producer["produce"](producer["ORIGINAL"], output, True)

    def test_unqualified_executable_is_refused(self):
        changed = self.root / "changed.so"
        raw = bytearray(producer["ORIGINAL"].read_bytes())
        raw[-1] ^= 1
        changed.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, "not admitted"):
            producer["produce"](changed, self.root / "bad-image", True)

    @unittest.skipUnless(os.environ.get("MAYHEM_EXACT_CANDIDATE"), "set MAYHEM_EXACT_CANDIDATE to test the qualified rebuild")
    def test_original_candidate_comparison(self):
        candidate = Path(os.environ["MAYHEM_EXACT_CANDIDATE"])
        output = self.root / "comparison"
        producer["produce"](candidate, output, False)
        result = verifier["verify"](output / "report.json", candidate)
        self.assertEqual("PASS", result["status"])
        self.assertEqual(14, result["equal_observed_behavior"])


if __name__ == "__main__":
    unittest.main()
