#!/usr/bin/env python3
"""Regression and admission tests for the cross-program lifecycle packet."""
from __future__ import annotations

import base64
import copy
import importlib.util
import sys
import shutil
import subprocess
from unittest.mock import patch
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify as reader  # noqa: E402
life = reader.lifecycle


class CrossProgramLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.control = life.run_suite(life.base.CAPTURED["pump_original"])
        cls.control["negative_controls"] = life.negative_controls(cls.control)

    def test_original_control_is_supported_and_equal(self):
        self.assertEqual(self.control["classification"], "equal_observed_behavior")
        self.assertEqual(self.control["mismatch_fields"], [])
        self.assertEqual(self.control["receipt_failures"], {"original": [], "candidate": []})
        self.assertEqual(self.control["invariant_failures"], {"original": [], "candidate": []})
        self.assertEqual(self.control["infrastructure_failures"], [])
        self.assertEqual(reader.verify(self.control, life.base.CAPTURED["pump_original"]), [])

    def test_plan_has_persistent_and_atomic_transitions(self):
        self.assertEqual(len(life.STEPS), 11)
        self.assertEqual(sum(len(step["operations"]) > 1 for step in life.STEPS), 2)
        names = [step["name"] for step in life.STEPS]
        self.assertLess(names.index("trade-A"), names.index("collect-A"))
        self.assertLess(names.index("admin-A-to-B"), names.index("trade-B"))
        self.assertLess(names.index("atomic-unswept-B-to-C"), names.index("atomic-sweep-B-to-C-retry"))
        self.assertLess(names.index("atomic-sweep-B-to-C-retry"), names.index("trade-C"))

    def test_transactions_are_genuinely_signed_and_program_routed(self):
        program_for = {
            "amm_buy_v2": life.AMM,
            "amm_sweep_creator_fee": life.AMM,
            "amm_collect_creator_fee": life.AMM,
            "pump_admin_cto": life.PUMP,
            "pump_collect_creator_fee": life.PUMP,
        }
        for side in ("original", "candidate"):
            signatures = []
            for row, plan in zip(self.control[side]["receipts"], life.STEPS):
                tx = life.Transaction.from_bytes(base64.b64decode(row["transaction_base64"], validate=True))
                self.assertEqual(list(tx.verify_with_results()), [True] * tx.message.header.num_required_signatures)
                self.assertEqual(len(tx.message.instructions), 1 + len(plan["operations"]))
                routed = [tx.message.account_keys[ix.program_id_index] for ix in tx.message.instructions[1:]]
                self.assertEqual(routed, [program_for[operation["op"]] for operation in plan["operations"]])
                signers = set(tx.message.account_keys[:tx.message.header.num_required_signatures])
                self.assertTrue(signers <= {life.PAYER.pubkey(), life.ADMIN.pubkey()})
                self.assertNotIn(life.Harness._mint_fixture(0, "native").pool_authority, signers)
                signatures.append(str(tx.signatures[0]))
            self.assertEqual(len(signatures), len(set(signatures)))

    def test_fixture_addresses_are_canonical(self):
        harness = life.Harness(life.base.CAPTURED["pump_original"])
        fixture = harness.fixture
        self.assertEqual(fixture.curve, life.base.pda(b"bonding-curve", bytes(fixture.mint)))
        self.assertEqual(fixture.pool_authority, life.base.pda(b"pool-authority", bytes(fixture.mint)))
        expected_pool = life.base.pda(
            b"pool", bytes(2), bytes(fixture.pool_authority), bytes(fixture.mint), bytes(fixture.quote),
            program=life.AMM,
        )
        self.assertEqual(fixture.pool, expected_pool)
        self.assertEqual(harness.pool_base, life.base.ata(fixture.pool, fixture.mint, life.TOKEN))
        self.assertEqual(harness.pool_quote, life.base.ata(fixture.pool, fixture.quote, life.TOKEN))

    def test_failure_rolls_back_trade_before_failing_admin(self):
        for side in ("original", "candidate"):
            row = next(item for item in self.control[side]["receipts"]
                       if item["step"] == "atomic-unswept-B-to-C")
            self.assertIn("CreatorFeesNotSwept", row["outcome"])
            self.assertTrue(row["rollback_nonfee_equal"])
            self.assertEqual(
                {k: v for k, v in row["before"].items() if k != str(life.PAYER.pubkey())},
                {k: v for k, v in row["after"].items() if k != str(life.PAYER.pubkey())},
            )

    def test_negative_controls_hit_strict_comparator(self):
        self.assertEqual(self.control["negative_controls"], {
            "error": True, "after": True, "events": True, "inner_instructions": True,
        })

    def test_expected_failure_binds_numeric_error_and_instruction_index(self):
        for replacement in (
            "TransactionErrorInstructionError((2, Tagged(InstructionErrorCustom(6082))))",
            "TransactionErrorInstructionError((1, Tagged(InstructionErrorCustom(6081))))",
        ):
            changed = copy.deepcopy(self.control)
            for side in ("original", "candidate"):
                row = changed[side]["receipts"][5]
                row["error"] = replacement
                self.assertEqual(life.validate_run(changed[side]), [])
                self.assertIn("atomic-unswept-B-to-C:wrong-error", life.lifecycle_invariants(changed[side]))
            self.assertTrue(reader.verify(changed, life.base.CAPTURED["pump_original"]))

    def test_reader_rejects_tampered_receipts_and_cached_summaries(self):
        mutations = {}

        changed = copy.deepcopy(self.control)
        changed["candidate"]["receipts"][0]["error"] = "forged"
        mutations["error"] = changed

        changed = copy.deepcopy(self.control)
        changed["candidate"]["receipts"][0]["after"]["forged"] = None
        mutations["state"] = changed

        changed = copy.deepcopy(self.control)
        row = changed["candidate"]["receipts"][0]
        raw = bytearray(base64.b64decode(row["transaction_base64"], validate=True))
        raw[0] ^= 1
        row["transaction_base64"] = base64.b64encode(raw).decode()
        mutations["signature"] = changed

        changed = copy.deepcopy(self.control)
        changed["classification"] = "equal_observed_behavior"
        changed["mismatch_fields"] = ["forged"]
        mutations["summary"] = changed

        changed = copy.deepcopy(self.control)
        changed["candidate_provenance"]["candidate_sha256"] = "0" * 64
        mutations["provenance"] = changed

        for name, report in mutations.items():
            with self.subTest(name=name):
                self.assertTrue(reader.verify(report, life.base.CAPTURED["pump_original"]))

    def test_reader_binds_signed_message_to_exact_instructions(self):
        changed = copy.deepcopy(self.control)
        for side in ("original", "candidate"):
            row = changed[side]["receipts"][0]
            old = life.Transaction.from_bytes(base64.b64decode(row["transaction_base64"]))
            replacement = life.Transaction.new_signed_with_payer(
                [life.set_compute_unit_limit(1_400_000)], life.PAYER.pubkey(),
                [life.PAYER], old.message.recent_blockhash,
            )
            row.update(transaction_base64=base64.b64encode(bytes(replacement)).decode(),
                       signature=str(replacement.signatures[0]),
                       signature_verification=list(replacement.verify_with_results()),
                       message_sha256=life.base.sha(bytes(replacement.message)))
        changed["mismatch_fields"], changed["comparison"] = life.compare_runs(
            changed["original"], changed["candidate"]
        )
        # Both rows have genuine signatures and agree with each other, but
        # neither message executes the claimed trade.
        self.assertEqual(changed["mismatch_fields"], [])
        self.assertIn("trade-A:signed-instruction-plan", life.validate_run(changed["original"]))
        self.assertTrue(reader.verify(changed, life.base.CAPTURED["pump_original"]))

    def test_reader_rejects_coerced_signature_and_count_claims(self):
        for replacement in ([1], [1.0]):
            changed = copy.deepcopy(self.control)
            for side in ("original", "candidate"):
                changed[side]["receipts"][0]["signature_verification"] = replacement
            self.assertIn("trade-A:signature-verification", life.validate_run(changed["original"]))
            self.assertTrue(reader.verify(changed, life.base.CAPTURED["pump_original"]))
        changed = copy.deepcopy(self.control)
        changed["transaction_count_per_image"] = 11.0
        self.assertIn("transaction_count_per_image", reader.verify(changed, life.base.CAPTURED["pump_original"]))

    def test_snapshot_membership_covers_constructed_unused_accounts(self):
        changed = copy.deepcopy(self.control)
        key = str(life.CREATORS[3].pubkey())
        for side in ("original", "candidate"):
            for row in changed[side]["receipts"]:
                for stage in ("before", "after"):
                    row[stage].pop(key)
                    row[stage + "_hash"] = life.base.canonical_hash(row[stage])
            changed[side]["initial_state_hash"] = changed[side]["receipts"][0]["before_hash"]
        self.assertIn("trade-A:before-membership", life.validate_run(changed["original"]))
        self.assertTrue(reader.verify(changed, life.base.CAPTURED["pump_original"]))

    def test_plan_change_is_rejected_before_any_execution(self):
        with patch.object(life, "STEPS", life.STEPS[:-1]), patch.object(life, "run_image") as run:
            with self.assertRaisesRegex(ValueError, "plan changed"):
                life.run_suite(life.base.CAPTURED["pump_original"])
            run.assert_not_called()

    def test_reader_refuses_duplicate_fields_and_malformed_rows(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"schema":"first","schema":"second"}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON field"):
                reader.read_report(path)
            for constant in ("NaN", "Infinity", "-Infinity"):
                path.write_text('{"unknown":' + constant + '}')
                with self.assertRaisesRegex(ValueError, "non-finite JSON constant"):
                    reader.read_report(path)
        for payload in (None, {}, {"original": []}, dict(self.control, original={"receipts": None})):
            self.assertTrue(reader.verify(payload, life.base.CAPTURED["pump_original"]))

    def test_changed_private_producer_input_fails_before_execution(self):
        # Copy only the imported source/metadata cohort. The candidate and
        # captured images deliberately do not exist: admission must run first.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source in life.PRODUCER_PATHS:
                target = root / source.relative_to(life.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            script = root / Path(life.__file__).relative_to(life.ROOT)
            code = (
                'import sys; from pathlib import Path; from unittest.mock import patch; '
                'sys.path.insert(0,sys.argv[1]); import lifecycle as life; '
                'life.VERIFIER_PATH.write_bytes(life.VERIFIER_PATH.read_bytes()+b"# changed\\n"); '
                '\nwith patch.object(life,"run_image") as run:\n'
                ' try: life.run_suite(Path("missing-candidate.so"))\n'
                ' except ValueError as error: assert "producer input changed" in str(error)\n'
                ' else: raise AssertionError("changed helper admitted")\n'
                ' run.assert_not_called()\n'
            )
            result = subprocess.run([sys.executable, '-B', '-c', code, str(script.parent)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reader_ignores_timestamp_valid_executable_bytecode_caches(self):
        import importlib._bootstrap_external as bytecode
        for source in (Path(life.__file__), life.BASE_PATH,
                       life.ROOT / "scripts/pump_differential_output.py"):
            with self.subTest(source=source.name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                for original in life.PRODUCER_PATHS:
                    target = root / original.relative_to(life.ROOT)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(original, target)
                target = root / source.relative_to(life.ROOT)
                marker = root / "unadmitted-code-ran"
                injected = compile(f"from pathlib import Path; Path({str(marker)!r}).write_text('ran'); "
                                   "raise RuntimeError('unadmitted cached code')", str(target), 'exec')
                cached = Path(importlib.util.cache_from_source(str(target)))
                cached.parent.mkdir(exist_ok=True)
                stat = target.stat()
                cached.write_bytes(bytecode._code_to_timestamp_pyc(injected, int(stat.st_mtime), stat.st_size))
                # Prove this is a valid, executable cache to the normal loader.
                control = ('import importlib.util,sys; s=importlib.util.spec_from_file_location("control",sys.argv[1]); '
                           'm=importlib.util.module_from_spec(s); s.loader.exec_module(m)')
                result = subprocess.run([sys.executable, '-B', '-c', control, str(target)],
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(marker.exists())
                marker.unlink()
                folder = root / HERE.relative_to(life.ROOT)
                code = 'import sys; sys.path.insert(0,sys.argv[1]); import verify; verify.lifecycle.recheck_inputs()'
                result = subprocess.run([sys.executable, '-B', '-c', code, str(folder)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(marker.exists())

    def test_output_cannot_add_a_file_inside_the_source_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "programs/pump"
            source.mkdir(parents=True)
            (source / "input.rs").write_text("unchanged")
            output = source / "new-report.json"
            with patch.object(life, "ROOT", root), patch.object(life, "run_suite") as run, \
                 patch.object(sys, "argv", ['lifecycle.py', '--candidate', str(life.base.CAPTURED['pump_original']),
                                             '--output', str(output)]):
                with self.assertRaisesRegex(ValueError, "aliases an input"):
                    life.main()
                run.assert_not_called()
            self.assertFalse(output.exists())
            self.assertEqual((source / "input.rs").read_text(), "unchanged")

    def test_canonical_report_bytes_are_deterministic_and_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.json.gz"
            second = Path(temporary) / "second.json.gz"
            life.write_report(first, self.control)
            life.write_report(second, self.control)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with self.assertRaises(FileExistsError):
                life.write_report(first, self.control)


if __name__ == "__main__":
    unittest.main()
