#!/usr/bin/env python3
import base64
import copy
import sys
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import corpus as P  # noqa: E402
C = P.source_module("case_model", HERE / "case_model.py")
E = P.source_module("executor", HERE / "executor.py", imports={"case_model": C, "corpus": P})


def fixture_case(*, mutations=None, steps=None, mode="native"):
    case = {
        "schema": C.SCHEMA,
        "generator": C.GENERATOR,
        "root_seed": 7,
        "case_index": 0,
        "case_seed": C.derive_case_seed(7, 0),
        "config": {"mints": [mode], "shared": False, "complete": False,
                   "holder_initial": False, **({"native_vault_lamports": 890_880}
                   if mode == "native" else {"spl_vault_tokens": 100, "amm_tokens": 100})},
        "initial_mutations": mutations or [],
        "steps": steps or [{"name": "A-to-B", "op": "admin_cto", "new": 1}],
    }
    case["case_id"] = C.case_identity(case)
    return C.validate_case(case)


class ExecutorTests(unittest.TestCase):
    original = E.L.CAPTURED["pump_original"]

    def test_original_vs_original_is_equal_and_independently_signed(self):
        result = E.execute_case(fixture_case(), self.original, self.original)
        self.assertEqual(result["classification"], "equal_observed_behavior")
        self.assertEqual(result["invariant_failures"], {"original": [], "candidate": []})
        left, right = result["original"], result["candidate"]
        self.assertIsNot(left, right)
        self.assertIsNot(left["receipts"][0]["after"], right["receipts"][0]["after"])
        self.assertTrue(all(left["receipts"][0]["signature_verification"]))
        self.assertEqual(left["receipts"][0]["transaction_base64"],
                         right["receipts"][0]["transaction_base64"])

    def test_account_mutation_is_encoded_before_execution(self):
        case = fixture_case(mutations=[{"target": "curve", "action": "set_byte",
                                       "offset": 48, "value": 1}])
        harness = E.FuzzHarness(self.original, case)
        curve = harness.vm.get_account(harness.mints[0].curve)
        self.assertEqual(curve.data[48], 1)
        result = E.execute_case(case, self.original, self.original)
        self.assertEqual(result["classification"], "equal_observed_behavior")

    def test_invalid_truncated_data_is_program_behavior_not_success_or_infra(self):
        case = fixture_case(mutations=[{"target": "curve", "action": "truncate", "value": 8}])
        result = E.execute_case(case, self.original, self.original)
        self.assertEqual(result["classification"], "equal_observed_behavior")
        self.assertIsNotNone(result["original"]["receipts"][0]["error"])
        self.assertEqual(result["original"]["receipts"][0]["failure_class"], "program")
        self.assertTrue(result["original"]["receipts"][0]["rollback_nonfee_equal"])

    def test_pda_accounts_are_never_fabricated_as_signers(self):
        result = E.execute_case(fixture_case(), self.original, self.original)
        accounts = result["original"]["receipts"][0]["instruction_accounts"]
        fixture = E.L.Harness(self.original, {"mints": ["native"]}).mints[0]
        pdas = {str(fixture.curve), str(fixture.pool), str(fixture.sharing),
                str(fixture.pool_authority)}
        self.assertFalse(any(row["signer"] for row in accounts if row["pubkey"] in pdas))

    def test_replaced_required_signer_uses_retained_real_keypair(self):
        case = fixture_case(steps=[{"name": "replace-admin", "op": "admin_cto", "new": 1,
                                   "replace_accounts": [{"index": 0, "creator": 3}]}])
        result = E.execute_case(case, self.original, self.original)
        self.assertEqual(result["classification"], "equal_observed_behavior")
        receipt = result["original"]["receipts"][0]
        self.assertTrue(all(receipt["signature_verification"]))
        self.assertEqual(receipt["instruction_accounts"][0]["pubkey"], str(E.L.CREATORS[3].pubkey()))

    def test_unsupported_fixture_is_never_counted_as_equivalence(self):
        case = fixture_case(mutations=[{"target": "curve", "action": "truncate", "value": 8},
                                       {"target": "curve", "action": "set_byte",
                                        "offset": 48, "value": 1}])
        result = E.execute_case(case, self.original, self.original)
        self.assertEqual(result["classification"], "unsupported_fixture")
        self.assertNotIn("original", result)

    def test_behavior_comparator_detects_real_observable_changes(self):
        run = E.run_image(self.original, fixture_case())
        changed = copy.deepcopy(run)
        changed["receipts"][0]["after"][str(E.L.GLOBAL)]["lamports"] += 1
        fields, _ = E.compare_runs(run, changed)
        self.assertIn("A-to-B:after", fields)
        self.assertTrue(E.validate_run(changed, fixture_case()))

    def test_corrupted_transaction_receipt_fails_validation(self):
        run = E.run_image(self.original, fixture_case())
        raw = bytearray(base64.b64decode(run["receipts"][0]["transaction_base64"]))
        raw[-1] ^= 1
        run["receipts"][0]["transaction_base64"] = base64.b64encode(raw).decode()
        self.assertTrue(E.validate_run(run, fixture_case()))

    def test_extension_panic_is_infrastructure_but_interrupt_propagates(self):
        class ExtensionPanic(BaseException):
            pass

        with mock.patch.object(E, "run_image", side_effect=ExtensionPanic("bounded panic")):
            result = E.execute_case(fixture_case(), self.original, self.original)
        self.assertEqual(result["classification"], "infrastructure_failure")
        self.assertIn("ExtensionPanic", result["reason"])
        with mock.patch.object(E, "run_image", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                E.execute_case(fixture_case(), self.original, self.original)


class ReceiptAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = fixture_case()
        cls.saved_run = E.run_image(E.L.CAPTURED["pump_original"], cls.case)

    def _reject(self, mutate):
        changed = copy.deepcopy(self.saved_run)
        mutate(changed)
        self.assertTrue(E.validate_run(changed, self.case), changed)

    def test_dry_fixture_reconstructs_initial_state_without_vm_execution(self):
        with mock.patch.object(E.L, "LiteSVM", side_effect=AssertionError("no VM")):
            fixture = E.fixture_plan(self.case)
            self.assertEqual(fixture.snapshot(), self.saved_run["receipts"][0]["before"])
            self.assertEqual(E.validate_run(self.saved_run, self.case), [])

    def test_dry_fixture_matches_host_storage_across_modes_and_zero_accounts(self):
        for mode in ("native", "spl", "token22"):
            for target in (None, "global", "curve"):
                with self.subTest(mode=mode, zero=target):
                    mutations = [] if target is None else [{"target": target, "action": "lamports", "value": 0}]
                    case = fixture_case(mode=mode, mutations=mutations)
                    expected = E.FuzzHarness(E.L.CAPTURED["pump_original"], case).snapshot()
                    self.assertEqual(E.fixture_plan(case).snapshot(), expected)

    def test_signed_unrelated_pump_message_is_rejected(self):
        from solders.instruction import Instruction
        from solders.compute_budget import set_compute_unit_limit
        from solders.hash import Hash
        from solders.transaction import Transaction
        def mutate(run):
            row = run["receipts"][0]
            instruction = Instruction(E.L.PUMP, b"unrelated", [])
            tx = Transaction.new_signed_with_payer(
                [set_compute_unit_limit(1_400_000), instruction], E.L.PAYER.pubkey(),
                [E.L.PAYER], Hash.from_string(row["recent_blockhash"]))
            row.update(transaction_base64=base64.b64encode(bytes(tx)).decode(),
                       instruction_data_base64=base64.b64encode(bytes(instruction.data)).decode(),
                       instruction_accounts=[], signature=str(tx.signatures[0]),
                       signature_verification=list(tx.verify_with_results()),
                       message_sha256=E.sha(bytes(tx.message)))
        self._reject(mutate)

    def test_extra_signed_instruction_is_rejected(self):
        from solders.compute_budget import set_compute_unit_limit
        from solders.hash import Hash
        from solders.transaction import Transaction
        def mutate(run):
            row = run["receipts"][0]
            fixture = E.fixture_plan(self.case)
            instruction = fixture.admin_instruction(self.case["steps"][0])
            tx = Transaction.new_signed_with_payer(
                [set_compute_unit_limit(1), set_compute_unit_limit(1_400_000), instruction],
                E.L.PAYER.pubkey(), fixture._signers(instruction),
                Hash.from_string(row["recent_blockhash"]))
            row.update(transaction_base64=base64.b64encode(bytes(tx)).decode(),
                       signature=str(tx.signatures[0]), signature_verification=list(tx.verify_with_results()),
                       message_sha256=E.sha(bytes(tx.message)))
        self._reject(mutate)

    def test_signature_and_account_flags_are_exact_booleans(self):
        self._reject(lambda run: run["receipts"][0].update(
            signature_verification=[1] * len(run["receipts"][0]["signature_verification"])))
        self._reject(lambda run: run["receipts"][0]["instruction_accounts"][0].update(signer=1))
        self._reject(lambda run: run["receipts"][0]["instruction_accounts"][0].update(writable=not run["receipts"][0]["instruction_accounts"][0]["writable"]))

    def test_omitted_and_foreign_initial_snapshot_reseal_is_rejected(self):
        def omit(run):
            row = run["receipts"][0]
            for stage in ("before", "after"):
                row[stage].pop(str(E.L.GLOBAL))
                row[stage + "_hash"] = E.L.canonical_hash(row[stage])
            run["initial_state_hash"] = row["before_hash"]
        self._reject(omit)
        def foreign(run):
            row = run["receipts"][0]
            for stage in ("before", "after"):
                row[stage][str(E.L.GLOBAL)]["lamports"] += 1
                row[stage + "_hash"] = E.L.canonical_hash(row[stage])
            run["initial_state_hash"] = row["before_hash"]
        self._reject(foreign)

    def test_metadata_types_empty_runs_and_wrong_roles_are_rejected(self):
        self._reject(lambda run: run["receipts"][0]["after"][str(E.L.GLOBAL)].update(executable=0))
        self._reject(lambda run: run["receipts"][0]["after"][str(E.L.GLOBAL)].update(rent_epoch=True))
        self._reject(lambda run: run.update(receipts=[]))
        self._reject(lambda run: run["mint_accounts"][0].update(curve=str(E.L.GLOBAL)))

    def test_excluded_classification_needs_independent_fixture_admission(self):
        record = {"schema": E.SCHEMA, "case": self.case, "case_id": self.case["case_id"],
                  "classification": "unsupported_fixture", "reason": "fabricated"}
        self.assertTrue(E.validate_result(record, self.case))
        record["classification"] = "infrastructure_failure"
        self.assertTrue(E.validate_result(record, self.case))
        unsupported = fixture_case(mutations=[{"target": "curve", "action": "truncate", "value": 8},
                                              {"target": "curve", "action": "set_byte", "offset": 48, "value": 1}])
        with mock.patch.object(E, "run_image", side_effect=AssertionError("no VM execution")):
            result = E.execute_case(unsupported, Path("unused"), Path("unused"))
        self.assertEqual(result["classification"], "unsupported_fixture")
        self.assertEqual(E.validate_result(result, unsupported), [])

    def test_noncanonical_original_is_rejected_before_vm_execution(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            original = Path(temp) / "not-the-original.so"
            original.write_bytes(b"different image")
            with mock.patch.object(E, "run_image", side_effect=AssertionError("no VM execution")):
                result = E.execute_case(self.case, original, original)
            self.assertEqual(result["classification"], "infrastructure_failure")
            self.assertIn("not the captured Pump Main", result["reason"])
            self.assertTrue(E.validate_result(result, self.case))

    def test_guest_trap_and_budget_exhaustion_are_program_observations(self):
        self.assertEqual(E.failure_class("ProgramFailedToComplete"), "program")
        self.assertEqual(E.failure_class("ComputationalBudgetExceeded"), "program")
        self.assertEqual(E.failure_class("BlockhashNotFound"), "infrastructure")

    def test_private_closure_ignores_canonical_module_poison(self):
        import types
        fake = types.ModuleType("pump_differential_output")
        fake.PumpReport = object()
        previous = sys.modules.get("pump_differential_output")
        sys.modules["pump_differential_output"] = fake
        try:
            loaded = P.source_module("executor", HERE / "executor.py")
            self.assertIs(sys.modules["pump_differential_output"], fake)
            self.assertIsNot(loaded.L.PumpReport, fake.PumpReport)
            self.assertEqual(loaded.fixture_plan(self.case).snapshot(), self.saved_run["receipts"][0]["before"])
        finally:
            if previous is None:
                sys.modules.pop("pump_differential_output", None)
            else:
                sys.modules["pump_differential_output"] = previous


    def test_valid_timestamp_pyc_cannot_replace_lifecycle_helper_source(self):
        import importlib.util
        import os
        import py_compile
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            source_paths = [HERE / name for name in ("corpus.py", "case_model.py", "executor.py")]
            source_paths += [Path(E.L.__source_path__), E.L.IDL_PATH, E.L.CONFIG_PATH,
                             E.ROOT / "scripts/pump_differential_output.py"]
            for source in source_paths:
                target = root / source.relative_to(E.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            helper = root / "scripts/pump_differential_output.py"
            clean = helper.read_bytes()
            marker = Path(temp) / "cached-code-executed"
            malicious = ("from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('bad')\n").encode()
            malicious += b"#" * (len(clean) - len(malicious))
            self.assertEqual(len(malicious), len(clean))
            helper.write_bytes(malicious)
            os.utime(helper, (1_700_000_000, 1_700_000_000))
            py_compile.compile(str(helper), doraise=True)
            helper.write_bytes(clean)
            os.utime(helper, (1_700_000_000, 1_700_000_000))
            spec = importlib.util.spec_from_file_location("_cached_fuzzer_control", helper)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertTrue(marker.exists(), "negative control must prove cache executable")
            marker.unlink()
            import types
            private_loader = types.ModuleType("_temporary_raw_loader")
            private_loader.__file__ = str(root / (HERE / "corpus.py").relative_to(E.ROOT))
            exec(compile(Path(private_loader.__file__).read_bytes(), private_loader.__file__, "exec"),
                 private_loader.__dict__)
            loaded = private_loader.source_module("executor", root / (HERE / "executor.py").relative_to(E.ROOT))
            self.assertFalse(marker.exists())
            self.assertEqual(loaded.fixture_plan(self.case).snapshot(), self.saved_run["receipts"][0]["before"])
            self.assertEqual(loaded.RUNTIME_SOURCE_HASHES[str(helper.resolve())], E.sha(clean))


if __name__ == "__main__":
    unittest.main()
