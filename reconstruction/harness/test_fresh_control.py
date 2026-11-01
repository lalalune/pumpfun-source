#!/usr/bin/env python3
"""Synthetic fresh-control build/score tests; no compiler is invoked."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

from fresh_control_inputs import load_context

CONTEXT = load_context()
fresh_control = CONTEXT.load("fresh_control")


def crate(path: Path, value: int) -> Path:
    (path / "src").mkdir(parents=True)
    (path / "Cargo.toml").write_text('[package]\nname="fixture"\nversion="0.0.0"\n', encoding="utf-8")
    (path / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
    (path / "src/lib.rs").write_text(f"pub fn value() -> u64 {{ {value} }}\n", encoding="utf-8")
    return path


def row(normalized: bool, raw: bool, size: int = 8, symbols=None) -> dict:
    return {
        "bytes": size,
        "normalized": normalized,
        "raw": raw,
        "symbols": list(symbols or (["fixture"] if normalized else [])),
    }


class FreshControlTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fresh-control-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = crate(self.root / "base", 1)
        self.candidate = crate(self.root / "candidate", 2)
        self.build_order = []
        self.windows = {
            "base": {0x100: row(True, True), 0x108: row(False, False)},
            "candidate": {0x100: row(True, True), 0x108: row(True, False)},
        }

        def copy_inputs(source, destination):
            (destination / "original.so").write_bytes(b"captured original")
            (destination / "functions.tsv").write_text("synthetic inventory\n", encoding="utf-8")

        def build(source, work, output, **kwargs):
            side = "base" if Path(source) == self.base.resolve() else "candidate"
            self.build_order.append((side, Path(work), Path(output)))
            output.mkdir(parents=True)
            image = output / "unstripped.so"
            image.write_bytes(side.encode())
            (output / "candidate.so").write_bytes((side + "-stripped").encode())
            (output / "build.log").write_text("deterministic synthetic build\n", encoding="utf-8")
            return {
                "ok": True,
                "runtime_valid": True,
                "stack_warnings": [],
                "recipe": "identity",
                "triple": "sbpf-solana-solana",
                "source_sha256": fresh_control.snapshot(source)["sha256"],
                "unstripped_sha256": fresh_control.sha256_file(image),
                "candidate_sha256": fresh_control.sha256_file(output / "candidate.so"),
            }
        self.fake_build = build

        def score(image, expected):
            side = Path(image).read_bytes().decode()
            self.assertEqual(fresh_control.sha256_file(image), expected)
            return self.windows[side], expected

        self.patchers = [
            mock.patch.object(fresh_control, "copy_original_inputs", side_effect=copy_inputs),
            mock.patch.object(fresh_control, "_binding", return_value={"tools": {"score.py": "pinned"}}),
            mock.patch.object(fresh_control.fastbuild, "build", side_effect=build),
            mock.patch.object(fresh_control.official_score, "score_with_hash", side_effect=score),
            mock.patch.object(fresh_control.fastbuild, "SDK", self.root / "sdk"),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(self.patchers)])

    def run_pair(self, name="out"):
        return fresh_control.run_pair(
            self.base,
            self.candidate,
            self.root / name,
            sdk=self.root / "sdk",
            hybrid=self.root / "hybrid",
        )

    def test_positive_gain_is_accepted_after_two_isolated_builds(self):
        receipt = self.run_pair()
        self.assertTrue(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["comparison"]["normalized_gains"], ["0x108"])
        self.assertEqual(receipt["comparison"]["normalized_losses"], [])
        self.assertEqual([entry[0] for entry in self.build_order], ["base", "candidate"])
        self.assertNotEqual(self.build_order[0][1], self.build_order[1][1])
        self.assertEqual(receipt["sources"]["base"]["sha256"], fresh_control.snapshot(self.base)["sha256"])
        self.assertIn("base-build/unstripped.so", receipt["artifacts"])
        self.assertIn("candidate-score.json", receipt["artifacts"])

    def test_normalized_regression_is_rejected(self):
        self.windows["candidate"][0x100] = row(False, False)
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertIn("normalized_match_regression", receipt["qualification"]["rejection_reasons"])
        self.assertEqual(receipt["comparison"]["normalized_losses"], ["0x100"])

    def test_raw_regression_is_rejected_even_when_normalized_match_survives(self):
        self.windows["candidate"][0x100] = row(True, False)
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["comparison"]["normalized_losses"], [])
        self.assertEqual(receipt["comparison"]["raw_losses"], ["0x100"])
        self.assertIn("raw_match_regression", receipt["qualification"]["rejection_reasons"])

    def test_changed_inventory_is_rejected(self):
        self.windows["candidate"][0x110] = row(False, False)
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["comparison"]["added"], ["0x110"])
        self.assertIn("added_windows", receipt["qualification"]["rejection_reasons"])

    def test_ambiguous_membership_is_reported(self):
        self.windows["candidate"][0x108] = row(True, False, symbols=["one", "two"])
        receipt = self.run_pair()
        self.assertEqual(receipt["scores"]["candidate"]["ambiguous"], ["0x108"])

    def test_missing_window_is_rejected(self):
        self.windows["candidate"].pop(0x108)
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["comparison"]["missing"], ["0x108"])
        self.assertIn("missing_windows", receipt["qualification"]["rejection_reasons"])

    def test_resized_window_is_rejected(self):
        self.windows["candidate"][0x108] = row(False, False, size=16)
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["comparison"]["resized"], ["0x108"])
        self.assertIn("resized_windows", receipt["qualification"]["rejection_reasons"])

    def test_candidate_compilation_failure_is_retained_and_rejected(self):
        def fail_candidate(source, work, output, **kwargs):
            if Path(source) == self.candidate.resolve():
                output.mkdir(parents=True)
                (output / "build.log").write_text("synthetic compiler failure\n", encoding="utf-8")
                return {"ok": False, "runtime_valid": False, "stack_warnings": []}
            return self.fake_build(source, work, output, **kwargs)

        fresh_control.fastbuild.build.side_effect = fail_candidate
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["candidate_build_invalid"])
        self.assertIn("candidate-build/build.log", receipt["artifacts"])
        self.assertNotIn("receipt.json", receipt["artifacts"])

    def test_build_source_digest_mismatch_is_rejected(self):
        def wrong_source(source, work, output, **kwargs):
            result = self.fake_build(source, work, output, **kwargs)
            if Path(source) == self.candidate.resolve():
                result["source_sha256"] = "0" * 64
            return result

        fresh_control.fastbuild.build.side_effect = wrong_source
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"],
                         ["candidate_build_source_mismatch"])
        self.assertNotIn("receipt.json", receipt["artifacts"])

    def test_build_artifact_digest_mismatch_is_rejected(self):
        def wrong_artifact(source, work, output, **kwargs):
            result = self.fake_build(source, work, output, **kwargs)
            if Path(source) == self.base.resolve():
                result["candidate_sha256"] = "f" * 64
            return result

        fresh_control.fastbuild.build.side_effect = wrong_artifact
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"],
                         ["base_build_artifact_mismatch"])
        self.assertNotIn("receipt.json", receipt["artifacts"])

    def test_stack_invalid_build_is_never_scored(self):
        def invalid_stack(source, work, output, **kwargs):
            result = self.fake_build(source, work, output, **kwargs)
            if Path(source) == self.base.resolve():
                result["runtime_valid"] = False
                result["stack_warnings"] = ["Stack offset exceeded max offset"]
            return result

        fresh_control.fastbuild.build.side_effect = invalid_stack
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["base_build_invalid"])
        self.assertEqual(receipt["scores"], {})

    def test_mid_build_source_mutation_is_rejected(self):
        def mutating_build(source, work, output, **kwargs):
            result = self.fake_build(source, work, output, **kwargs)
            if Path(source) == self.base.resolve():
                (Path(source) / "src/lib.rs").write_text("pub fn mutated() {}\n", encoding="utf-8")
            return result

        fresh_control.fastbuild.build.side_effect = mutating_build
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["infrastructure_failure"])
        self.assertIn("source inputs changed", receipt["qualification"]["detail"])
        self.assertEqual(receipt["scores"], {})

    def test_toolchain_input_mutation_is_rejected_before_scoring(self):
        fresh_control._binding.side_effect = [
            {"tools": {"score.py": "before"}},
            {"tools": {"score.py": "after"}},
        ]
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["toolchain_or_scorer_input_mutation"])
        self.assertEqual(receipt["scores"], {})

    def test_missing_scoring_inputs_produce_an_infrastructure_receipt(self):
        fresh_control.copy_original_inputs.side_effect = FileNotFoundError("missing original.so")
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["infrastructure_failure"])
        self.assertIn("missing original.so", receipt["qualification"]["detail"])
        self.assertTrue((self.root / "out/receipt.json").is_file())

    def test_corrupt_score_membership_is_rejected(self):
        fresh_control.official_score.score_with_hash.side_effect = [
            ({0x100: {"bytes": 7, "normalized": True, "raw": True, "symbols": ["bad"]}}, "bad"),
        ]
        receipt = self.run_pair()
        self.assertEqual(receipt["qualification"]["rejection_reasons"], ["infrastructure_failure"])
        self.assertIn("invalid byte length", receipt["qualification"]["detail"])

    def test_report_is_deterministic_across_output_directories(self):
        first = self.run_pair("one")
        first_bytes = (self.root / "one/receipt.json").read_bytes()
        self.build_order.clear()
        second = self.run_pair("two")
        second_bytes = (self.root / "two/receipt.json").read_bytes()
        self.assertEqual(first, second)
        self.assertEqual(first_bytes, second_bytes)

    def test_existing_output_is_rejected_before_a_build(self):
        (self.root / "collision").mkdir()
        with self.assertRaisesRegex(FileExistsError, "already exists"):
            self.run_pair("collision")
        self.assertEqual(self.build_order, [])

    def test_saved_receipt_is_canonical_json(self):
        receipt = self.run_pair()
        loaded = json.loads((self.root / "out/receipt.json").read_text())
        self.assertEqual(loaded, receipt)
        self.assertTrue((self.root / "out/receipt.json").read_bytes().endswith(b"\n"))

    def test_second_build_cannot_change_an_earlier_binary_or_score(self):
        for name in ("base-build/unstripped.so", "base-score.json"):
            with self.subTest(name=name):
                def mutate(source, work, output, **kwargs):
                    result = self.fake_build(source, work, output, **kwargs)
                    if Path(source) == self.candidate.resolve():
                        (output.parent / name).write_bytes(b"changed by second build")
                    return result
                fresh_control.fastbuild.build.side_effect = mutate
                receipt = self.run_pair(name.replace("/", "-"))
                self.assertFalse(receipt["qualification"]["accepted"])
                self.assertIn("earlier", receipt["qualification"]["detail"])

    def test_truthy_build_flags_are_not_successful_builds(self):
        for field, value in (("ok", 1), ("runtime_valid", "false"), ("timed_out", True)):
            with self.subTest(field=field):
                def bad_flags(source, work, output, **kwargs):
                    result = self.fake_build(source, work, output, **kwargs)
                    result[field] = value
                    return result
                fresh_control.fastbuild.build.side_effect = bad_flags
                receipt = self.run_pair(field)
                self.assertEqual(receipt["qualification"]["rejection_reasons"], ["base_build_invalid"])

    def test_source_root_link_is_refused_before_a_build(self):
        alias = self.root / "linked-source"
        alias.symlink_to(self.base, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "linked"):
            fresh_control.run_pair(alias, self.candidate, self.root / "linked-out")
        self.assertEqual(self.build_order, [])

    def test_external_hook_cache_injection_rejects_build(self):
        import os
        def inject(source, work, output, **kwargs):
            result = self.fake_build(source, work, output, **kwargs)
            Path(os.environ["PYTHONPYCACHEPREFIX"], "injected.pyc").write_bytes(b"cached code")
            return result
        fresh_control.fastbuild.build.side_effect = inject
        receipt = self.run_pair()
        self.assertFalse(receipt["qualification"]["accepted"])
        self.assertIn("bytecode cache", receipt["qualification"]["detail"])

    def test_atomic_fresh_receipt_publication_preserves_previous_document(self):
        target = self.root / "receipt.json"
        target.write_text('{"old": true}\n', encoding="utf-8")
        with mock.patch.object(fresh_control.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                fresh_control.publish_json(target, {"new": True})
        self.assertEqual(target.read_text(), '{"old": true}\n')
        self.assertEqual(list(self.root.glob(".receipt.json.*")), [])


if __name__ == "__main__":
    unittest.main()
