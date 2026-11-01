#!/usr/bin/env python3
"""Independent fresh-control verifier and negative-control tests."""
from __future__ import annotations

import json
import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import test_fresh_control

fresh_control = test_fresh_control.fresh_control
verify_fresh_control = test_fresh_control.CONTEXT.load("verify_fresh_control")


class VerifyFreshControlTests(unittest.TestCase):
    def setUp(self):
        test_fresh_control.FreshControlTests.setUp(self)
        # The producer's mocked binding is the verifier's admitted provenance.
        self.verifier_binding = mock.patch.object(
            verify_fresh_control.fresh_control, "_binding",
            return_value={"tools": {"score.py": "pinned"}},
        )
        self.verifier_binding.start()
        self.addCleanup(self.verifier_binding.stop)

    run_pair = test_fresh_control.FreshControlTests.run_pair

    def verify(self):
        return verify_fresh_control.verify(
            self.root / "out",
            sdk=self.root / "sdk",
            hybrid=self.root / "hybrid",
            base_source=self.base,
            candidate_source=self.candidate,
        )

    def rewrite_receipt(self, mutate):
        path = self.root / "out/receipt.json"
        document = json.loads(path.read_text())
        mutate(document)
        fresh_control.publish_json(path, document)

    def refresh_artifact(self, relative):
        self.rewrite_receipt(lambda document: document["artifacts"].__setitem__(
            relative,
            {
                "bytes": (self.root / "out" / relative).stat().st_size,
                "sha256": fresh_control.sha256_file(self.root / "out" / relative),
            },
        ))

    def test_independent_verifier_accepts_valid_receipt(self):
        self.run_pair()
        result = self.verify()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["comparison"]["normalized_gains"], ["0x108"])

    def test_negative_control_rejects_forged_acceptance_boolean(self):
        self.run_pair()
        self.rewrite_receipt(lambda document: document["qualification"].__setitem__("accepted", False))
        with self.assertRaisesRegex(ValueError, "acceptance boolean"):
            self.verify()

    def test_negative_control_rejects_changed_binary_even_with_inventory_rehashed(self):
        self.run_pair()
        image = self.root / "out/candidate-build/unstripped.so"
        image.write_bytes(b"changed candidate binary")
        self.refresh_artifact("candidate-build/unstripped.so")
        with self.assertRaisesRegex(ValueError, "unstripped.so digest mismatch"):
            self.verify()

    def test_negative_control_recomputes_score_comparison(self):
        self.run_pair()
        score_path = self.root / "out/candidate-score.json"
        document = json.loads(score_path.read_text())
        document["windows"]["256"].update(normalized=False, raw=False, symbols=[])
        changed_windows = {int(start): row for start, row in document["windows"].items()}
        document["summary"] = fresh_control.score_summary(changed_windows)
        fresh_control.publish_json(score_path, document)
        score_hash = fresh_control.sha256_file(score_path)
        def forge(receipt):
            receipt["scores"]["candidate"] = {
                "image_sha256": receipt["builds"]["candidate"]["unstripped_sha256"],
                **document["summary"],
                "report_sha256": score_hash,
            }
            receipt["artifacts"]["candidate-score.json"] = {
                "bytes": score_path.stat().st_size,
                "sha256": score_hash,
            }
        self.rewrite_receipt(forge)
        with self.assertRaisesRegex(ValueError, "actual ELF rescoring"):
            self.verify()

    def test_negative_control_rejects_wrong_admitted_source(self):
        self.run_pair()
        (self.candidate / "src/lib.rs").write_text("pub fn changed() {}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "candidate source does not match"):
            self.verify()

    def test_resealed_forged_match_cannot_override_actual_elf_scoring(self):
        self.run_pair()
        path = self.root / "out/candidate-score.json"
        score = json.loads(path.read_text())
        score["windows"]["264"].update(raw=True)
        score["summary"] = fresh_control.score_summary({int(k): v for k, v in score["windows"].items()})
        fresh_control.publish_json(path, score)
        def reseal(receipt):
            receipt["scores"]["candidate"] = {
                "image_sha256": receipt["builds"]["candidate"]["unstripped_sha256"],
                **score["summary"], "report_sha256": fresh_control.sha256_file(path),
            }
            receipt["comparison"] = verify_fresh_control.compare_scores.compare(
                verify_fresh_control.compare_scores.load_report(self.root / "out/base-score.json"),
                verify_fresh_control.compare_scores.load_report(path))
        self.rewrite_receipt(reseal)
        self.refresh_artifact("candidate-score.json")
        with self.assertRaisesRegex(ValueError, "actual ELF rescoring"):
            self.verify()

    def test_reader_rejects_coerced_flags_and_false_cold_claims(self):
        self.run_pair()
        path = self.root / "out/receipt.json"
        original = json.loads(path.read_text())
        for key, value in (("cold_targets", False), ("isolated_workspaces", 1), ("build_order", [])):
            changed = copy.deepcopy(original); changed[key] = value
            fresh_control.publish_json(path, changed)
            with self.assertRaisesRegex(ValueError, "build claims"):
                self.verify()
        for field, value in (("ok", 1), ("runtime_valid", "false"), ("timed_out", True)):
            changed = copy.deepcopy(original); changed["builds"]["base"][field] = value
            fresh_control.publish_json(path, changed)
            with self.assertRaisesRegex(ValueError, "build flags"):
                self.verify()
        changed = copy.deepcopy(original); changed["qualification"]["accepted"] = 1
        fresh_control.publish_json(path, changed)
        with self.assertRaisesRegex(ValueError, "acceptance boolean"):
            self.verify()

    def test_reader_refuses_linked_artifacts_and_directory_changes(self):
        self.run_pair()
        root = self.root / "out"
        outside = self.root / "outside"; outside.write_bytes(b"outside")
        (root / "linked").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "linked"):
            self.verify()
        (root / "linked").unlink()
        (root / "new-empty-directory").mkdir()
        with self.assertRaisesRegex(ValueError, "inventory"):
            self.verify()

    def test_receipt_cannot_change_during_independent_rescoring(self):
        self.run_pair()
        original = fresh_control.official_score.score_with_hash.side_effect
        path = self.root / "out/receipt.json"
        def rescore(*args):
            result = original(*args)
            changed = json.loads(path.read_text()); changed["unvalidated"] = True
            fresh_control.publish_json(path, changed)
            return result
        fresh_control.official_score.score_with_hash.side_effect = rescore
        with self.assertRaisesRegex(ValueError, "receipt changed"):
            self.verify()

    def test_reader_rejects_nonstandard_and_duplicate_json(self):
        path = self.root / "bad.json"
        for payload in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            path.write_text(payload)
            with self.assertRaises(ValueError):
                verify_fresh_control.load_document(path)


if __name__ == "__main__":
    unittest.main()
