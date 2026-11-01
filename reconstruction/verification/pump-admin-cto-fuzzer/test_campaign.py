#!/usr/bin/env python3
import json
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import campaign as C  # noqa: E402
import corpus as P  # noqa: E402
import executor as E  # noqa: E402


class CampaignTests(unittest.TestCase):
    original = E.L.CAPTURED["pump_original"]

    def test_original_control_is_repeatable_and_detects_negative_controls(self):
        with tempfile.TemporaryDirectory() as temp:
            first = C.run_campaign(original=self.original, candidate=self.original,
                                   output=Path(temp) / "first", seed=20261101, count=2)
            second = C.run_campaign(original=self.original, candidate=self.original,
                                    output=Path(temp) / "second", seed=20261101, count=2)
            self.assertEqual(first, second)
            self.assertEqual(first["classification_counts"]["different_behavior"], 0)
            self.assertEqual(first["classification_counts"]["infrastructure_failure"], 0)
            self.assertTrue(first["negative_controls"]["all_detected"])
            self.assertTrue((Path(temp) / "first/receipts").is_dir())

    def test_source_input_mutation_during_execution_prevents_publication(self):
        with tempfile.TemporaryDirectory() as temp:
            candidate = Path(temp) / "candidate.so"
            shutil.copyfile(self.original, candidate)

            def mutate(index, case, result):
                if index == 0:
                    candidate.write_bytes(candidate.read_bytes() + b"tamper")

            output = Path(temp) / "campaign"
            with self.assertRaisesRegex(RuntimeError, "changed during campaign"):
                C.run_campaign(original=self.original, candidate=candidate, output=output,
                               seed=20261101, count=1, after_case=mutate)
            self.assertFalse(output.exists())
            self.assertEqual(len(P.find_partial_attempts(output)), 1)

    def test_compact_mode_retains_progress_without_full_receipt_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "compact"
            summary = C.run_campaign(original=self.original, candidate=self.original,
                                     output=output, seed=20261101, count=1,
                                     detailed_receipts=False)
            self.assertFalse(summary["detailed_receipts"])
            self.assertFalse((output / "receipts").exists())
            self.assertEqual(len(list((output / "progress").glob("*.json"))), 1)

    def test_start_index_selects_a_disjoint_replayable_tranche(self):
        with tempfile.TemporaryDirectory() as temp:
            first = C.run_campaign(original=self.original, candidate=self.original,
                                   output=Path(temp) / "first", seed=9, count=1)
            second = C.run_campaign(original=self.original, candidate=self.original,
                                    output=Path(temp) / "second", seed=9, count=1,
                                    start_index=1)
            self.assertNotEqual(first["cases"][0]["case_id"], second["cases"][0]["case_id"])
            self.assertEqual(second["start_index"], 1)

    def test_invalid_operational_arguments_are_rejected_before_execution(self):
        invalid = ({"count": True}, {"detailed_receipts": 1},
                   {"reduce_mismatches": 0}, {"reduction_budget": True},
                   {"reduction_budget": 10_001},
                   {"expected_original_sha256": "0" * 64})
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(C.E, "execute_case") as execute:
            for index, changes in enumerate(invalid):
                output = Path(temp) / str(index)
                arguments = dict(original=self.original, candidate=self.original,
                                 output=output, seed=20261101, count=1)
                arguments.update(changes)
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    C.run_campaign(**arguments)
                self.assertFalse(output.exists())
            execute.assert_not_called()

    def test_callback_cannot_rewrite_retained_case_or_receipt(self):
        def mutate(index, case, result):
            case["steps"].clear()
            result.clear()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "copy-boundary"
            summary = C.run_campaign(original=self.original, candidate=self.original,
                                     output=output, seed=20261101, count=1,
                                     after_case=mutate)
            self.assertEqual(summary["classification_counts"]["equal_observed_behavior"], 1)
            retained = P.read_json(output / "cases.json")
            self.assertTrue(retained[0]["steps"])

    def test_invalid_executor_result_cannot_publish_a_complete_campaign(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(C.E, "execute_case", return_value={}):
            output = Path(temp) / "invalid"
            with self.assertRaisesRegex(ValueError, "invalid executed case receipt"):
                C.run_campaign(original=self.original, candidate=self.original,
                               output=output, seed=20261101, count=1)
            self.assertFalse(output.exists())
            partials = P.find_partial_attempts(output)
            self.assertEqual(len(partials), 1)
            self.assertTrue((partials[0] / "rejected/0000.json").is_file())

    def test_actual_compiled_self_bytes_are_bound_before_dependency_bootstrap(self):
        with tempfile.TemporaryDirectory(dir=C.ROOT) as temp:
            root = Path(temp)
            for source in C.PRODUCERS:
                target = root / source.relative_to(C.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
            source = root / HERE.relative_to(C.ROOT) / "campaign.py"
            compiled_sha = P.file_sha(source)
            proxy = types.ModuleType("types")
            proxy.__dict__.update(vars(types))
            changed = []
            def make_module(*args, **kwargs):
                if not changed:
                    source.write_bytes(source.read_bytes() + b"\n# changed during dependency bootstrap\n")
                    changed.append(True)
                return types.ModuleType(*args, **kwargs)
            proxy.ModuleType = make_module
            loaded = P.source_module("campaign", source, imports={"types": proxy})
            self.assertTrue(changed)
            self.assertEqual(loaded.SELF_SHA256, compiled_sha)
            self.assertNotEqual(loaded.SELF_SHA256, P.file_sha(source))
            with self.assertRaisesRegex(ValueError, "loaded producer source changed"):
                loaded.require_loaded_sources()


if __name__ == "__main__":
    unittest.main()
