#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest


HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("producer", HERE / "producer.py")
producer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(producer)


class ProducerTests(unittest.TestCase):
    def test_plan_covers_every_instruction(self):
        plan = producer.make_plan()
        self.assertEqual(len(plan["cases"]), 26)
        self.assertEqual({case["name"] for case in plan["cases"][1:]},
                         {row["name"] for row in producer.inventory.INSTRUCTIONS})

    def test_dispatch_has_no_signature_bypass(self):
        plan = producer.make_plan()
        self.assertFalse(any("sigverify" in step for case in plan["cases"] for step in case["steps"]))
        self.assertFalse(any("signed-event-authority" in step["label"] for step in plan["cases"][0]["steps"]))

    def test_each_instruction_has_account_and_decode_cases(self):
        for case in producer.make_plan()["cases"][1:]:
            labels = {step["label"] for step in case["steps"]}
            self.assertIn("recognized-disc-only", labels)
            self.assertIn("valid-args", labels)
            self.assertIn("one-account-short", labels)
            self.assertIn("source-order-unfunded", labels)
            self.assertIn("source-order-extra-account", labels)
            self.assertIn("first-fixed-program-wrong-id", labels)

    def test_negative_controls_detect_exact_field(self):
        plan = {"program_id": producer.inventory.PROGRAM_ID, "cases": [{"name": "dispatcher"}],
                "not_applicable_argument_families": ["bool", "enum", "vector"]}
        base = {field: None for field in producer.BEHAVIOR}
        base.update({"logs": [], "compute_units": 1, "error": None, "accounts": []})
        receipt = {"case": "dispatcher", "label": "x", "original": base, "candidate": dict(base)}
        report = producer.build_report(plan, [receipt], {})
        self.assertEqual(report["negative_controls"], {"changed_error_detected": True, "changed_state_detected": True})


if __name__ == "__main__":
    unittest.main()
