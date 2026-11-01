#!/usr/bin/env python3
"""Regression tests for the persistent PumpSwap multi-LP producer."""
from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import os
import py_compile
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import types
HERE = Path(__file__).resolve().parent
_admission = HERE / "admission.py"
_raw = _admission.read_bytes()
A = types.ModuleType("_lp_test_admission")
A.__file__ = str(_admission)
A.__source_sha256__ = __import__("hashlib").sha256(_raw).hexdigest()
exec(compile(_raw, str(_admission), "exec"), A.__dict__)
lifecycle = A.source_module("lifecycle", HERE / "lifecycle.py", bindings={"_ADMISSION": A})


class AdmissionTests(unittest.TestCase):
    def test_executable_timestamp_cache_is_ignored_and_namespaces_stay_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "local_helper.py"
            clean = b"MARKER = 'source'\n"
            cached = b"MARKER = 'cached'\n"
            self.assertEqual(len(clean), len(cached))
            path.write_bytes(cached)
            timestamp = path.stat().st_mtime_ns
            py_compile.compile(str(path), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
            path.write_bytes(clean)
            os.utime(path, ns=(timestamp, timestamp))
            spec = importlib.util.spec_from_file_location("_lp_actual_cache_control", path)
            ordinary = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ordinary)
            self.assertEqual(ordinary.MARKER, "cached")  # The cache really is executable.
            helper = types.ModuleType("_lp_isolated_admission")
            helper.__file__ = str(HERE / "admission.py")
            exec(compile(_raw, helper.__file__, "exec"), helper.__dict__)
            helper.ROOT, helper.LOADED = root, {}
            prior = dict(sys.modules)
            loaded = helper.source_module("local_helper", path)
            self.assertEqual(loaded.MARKER, "source")
            self.assertEqual(loaded.__source_sha256__, hashlib.sha256(clean).hexdigest())
            self.assertNotIn(loaded.__name__, sys.modules)
            self.assertTrue(all(sys.modules.get(name) is module for name, module in prior.items()))

    def test_direct_entrypoint_pins_self_before_local_dependency_bootstrap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for rel in A.snapshot_inputs():
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(A.ROOT / rel, target)
            package = root / HERE.relative_to(A.ROOT)
            admission = package / "admission.py"
            admission.write_bytes(admission.read_bytes() + b"\n_target = HERE / 'lifecycle.py'\n_target.write_bytes(_target.read_bytes() + b'\\n# bootstrap changed source\\n')\n")
            entrypoint = package / "lifecycle.py"
            code = ("import runpy; from pathlib import Path; "
                    f"loaded=runpy.run_path({str(entrypoint)!r}); "
                    "loaded['run_suite'](Path('unused-candidate'))")
            result = subprocess.run([sys.executable, "-I", "-B", "-c", code],
                                    capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("executed source/data differs", result.stderr)

    def test_strict_json_and_symlink_inputs_are_refused(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.assertRaises(ValueError):
                A.json_bytes(raw)
        self.assertFalse(A.same_json({"flag": True}, {"flag": 1}))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "source.py"
            target.write_text("pass\n")
            link = root / "link.py"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink"):
                A.regular_bytes(link, root=root)


class FixtureTests(unittest.TestCase):
    def test_provider_and_fee_keys_are_separate(self):
        keys = {lifecycle.FEE_PAYER.pubkey(), lifecycle.PROVIDER_A.pubkey(),
                lifecycle.PROVIDER_B.pubkey(), lifecycle.MINT_AUTHORITY.pubkey()}
        self.assertEqual(len(keys), 4)

    def test_canonical_pool_lp_and_ata_derivation(self):
        pool = lifecycle.PoolFixture.derive("case-0", index=0)
        expected_pool = lifecycle.Pubkey.find_program_address([
            b"pool", b"\0\0", bytes(lifecycle.PROVIDER_A.pubkey()),
            bytes(pool.base), bytes(pool.quote)], lifecycle.AMM)[0]
        self.assertEqual(pool.pool, expected_pool)
        self.assertEqual(pool.lp, lifecycle.Pubkey.find_program_address(
            [b"pool_lp_mint", bytes(pool.pool)], lifecycle.AMM)[0])
        self.assertNotEqual(pool.provider_accounts(lifecycle.PROVIDER_A)["lp"],
                            pool.provider_accounts(lifecycle.PROVIDER_B)["lp"])

    def test_case_plans_and_oracles_are_complete(self):
        plans = lifecycle.plans()
        self.assertEqual(len(plans), 9)
        self.assertEqual({plan["name"] for plan in plans}, set(lifecycle.EXPECTED_OUTCOMES))
        for plan in plans:
            self.assertEqual(len(plan["steps"]), len(lifecycle.EXPECTED_OUTCOMES[plan["name"]]))


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = lifecycle.run_suite(lifecycle.CAPTURED["original"])

    def test_original_vs_original_control(self):
        self.assertEqual(self.report["classification_counts"], {
            "equal_observed_behavior": 9, "different_behavior": 0,
            "unsupported_fixture": 0, "infrastructure_failure": 0})
        self.assertEqual(self.report["transaction_count_per_image"], 65)
        for row in self.report["cases"]:
            self.assertFalse(row["mismatch_fields"])
            self.assertFalse(row["oracle_mismatches"])

    def test_every_transaction_has_valid_real_signatures(self):
        for row in self.report["cases"]:
            for receipt in row["original"]["receipts"]:
                transaction = lifecycle.Transaction.from_bytes(
                    base64.b64decode(receipt["transaction_base64"], validate=True))
                required = transaction.message.header.num_required_signatures
                self.assertTrue(transaction.signatures and all(transaction.verify_with_results()))
                self.assertEqual(len(transaction.signatures), required)
                signers = list(transaction.message.account_keys[:required])
                self.assertEqual(signers[0], lifecycle.FEE_PAYER.pubkey())
                self.assertNotIn(row["fixture"]["pool"], receipt["signer_pubkeys"])

    def test_atomic_failure_rolls_back_complete_nonfee_state(self):
        row = next(row for row in self.report["cases"]
                   if row["case"] == "atomic-valid-deposit-invalid-withdraw-rollback")
        failed = row["original"]["receipts"][-1]
        self.assertEqual(failed["instruction_count"], 2)
        self.assertIsNotNone(failed["error"])
        self.assertTrue(failed["rollback_nonfee_equal"])

    def test_authority_and_overwithdraw_failures_are_program_errors(self):
        names = ("foreign-lp-authority-refused-then-owner-withdraws",
                 "over-withdraw-refused-then-partial-chain")
        for name in names:
            row = next(row for row in self.report["cases"] if row["case"] == name)
            failed = row["original"]["receipts"][5]
            self.assertEqual(failed["failure_class"], "program")
            self.assertTrue(failed["rollback_nonfee_equal"])
            self.assertEqual(row["original"]["receipts"][-1]["outcome"], "ok")

    def test_lp_and_reserve_conservation(self):
        for row in self.report["cases"]:
            final = row["original"]["receipts"][-1]["accounting"]["after"]
            self.assertEqual(final["locked_lp_difference"], 100)
            self.assertEqual(final["provider_lp_total"], final["lp_mint_supply"])
            self.assertEqual(final["base_total"], 2 * 10**12)

    def test_token2022_base_path_is_positive(self):
        row = next(row for row in self.report["cases"]
                   if row["case"] == "token2022-base-multi-provider")
        self.assertEqual(row["fixture"]["base_token_program"], str(lifecycle.TOKEN22))
        self.assertTrue(all(receipt["outcome"] == "ok" for receipt in row["original"]["receipts"]))

    def test_cross_pool_state_isolation(self):
        row = next(row for row in self.report["cases"]
                   if row["case"] == "two-pool-provider-state-isolation")
        primary = row["fixture"]
        baseline = row["original"]["receipts"][4]["after"]
        protected = [primary["pool"], primary["lp_mint"], primary["vault_base"],
                     primary["vault_quote"], primary["provider_a_accounts"]["base"],
                     primary["provider_b_accounts"]["base"]]
        for receipt in row["original"]["receipts"][5:]:
            for address in protected:
                self.assertEqual(receipt["before"][address], baseline[address])
                self.assertEqual(receipt["after"][address], baseline[address])

    def test_deterministic_replay(self):
        self.assertEqual(self.report, lifecycle.run_suite(lifecycle.CAPTURED["original"]))

    def test_first_prestate_is_exact_constructor_and_watch_set_never_grows(self):
        for index, (plan, row) in enumerate(zip(lifecycle.plans(), self.report["cases"])):
            harness = lifecycle.fixture_only(lifecycle.CAPTURED["original"], index, plan)
            for side in ("original", "candidate"):
                expected = harness.snapshot(side)
                self.assertEqual(row[side]["receipts"][0]["before"], expected)
                for receipt in row[side]["receipts"]:
                    self.assertEqual(set(receipt["before"]), set(expected))
                    self.assertEqual(set(receipt["after"]), set(expected))
                for before, after in zip(row[side]["receipts"], row[side]["receipts"][1:]):
                    self.assertEqual(before["after"], after["before"])

    def test_canonical_plan_construction_never_sends_a_transaction(self):
        from unittest import mock
        with mock.patch.object(lifecycle.LiteSVM, "send_transaction", side_effect=AssertionError("no VM execution")):
            for index, plan in enumerate(lifecycle.plans()):
                harness = lifecycle.fixture_only(lifecycle.CAPTURED["original"], index, plan)
                baseline = harness.snapshot("original")
                with mock.patch.object(lifecycle.LiteSVM, "set_account", side_effect=AssertionError("pure instruction construction")):
                    for number, step in enumerate(plan["steps"]):
                        name, instructions, signers, operation = lifecycle.plan_step(harness, step, number)
                        self.assertTrue(name and instructions and operation)
                        self.assertIn(lifecycle.FEE_PAYER.pubkey(), {pair.pubkey() for pair in signers})
                        self.assertNotIn(harness.pool.pool, {pair.pubkey() for pair in signers})
                        self.assertEqual(harness.snapshot("original"), baseline)

    def test_existing_and_dangling_outputs_are_refused_before_running(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            output.write_text("retain")
            with mock.patch.object(lifecycle, "run_suite", side_effect=AssertionError("no execution")):
                with self.assertRaises(FileExistsError):
                    lifecycle.produce(Path("unused"), output)
                output.unlink()
                output.symlink_to(Path(temporary) / "missing.json")
                with self.assertRaises(FileExistsError):
                    lifecycle.produce(Path("unused"), output)

    def test_runtime_suite_refuses_fabricated_build_receipts(self):
        with self.assertRaisesRegex(ValueError, "does not authenticate"):
            lifecycle.run_suite(Path("unused"), Path("invented-build-receipt.json"))

    def test_image_mutation_is_refused_without_publishing(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "candidate.so"
            raw = lifecycle.CAPTURED["original"].read_bytes()
            candidate.write_bytes(raw)
            saved = {case["case"]: case for case in self.report["cases"]}
            def controlled_reuse(_candidate, plan, *args):
                candidate.write_bytes(raw + b"mutation")
                return copy.deepcopy(saved[plan["name"]])
            output = Path(temporary) / "never-publish.json"
            with mock.patch.object(lifecycle, "run_plan", side_effect=controlled_reuse):
                with self.assertRaisesRegex(ValueError, "candidate changed"):
                    lifecycle.produce(candidate, output)
            self.assertFalse(output.exists())

    def test_normal_python_required_before_loading_a_vm(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, "-O", "-B", str(HERE / "lifecycle.py"), "--help"],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Normal Python is required", result.stderr)

    def test_exclusive_report_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json.gz"
            lifecycle.write_report(output, self.report)
            retained = output.read_bytes()
            with self.assertRaises(FileExistsError):
                lifecycle.write_report(output, {"tampered": True})
            self.assertEqual(output.read_bytes(), retained)


if __name__ == "__main__":
    unittest.main()
