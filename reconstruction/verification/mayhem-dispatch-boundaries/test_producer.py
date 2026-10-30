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



class VerifyTests(unittest.TestCase):
    def test_truncated_plan_is_rejected(self):
        import contextlib
        import io
        import json
        import sys
        import tempfile
        from unittest import mock

        vspec = importlib.util.spec_from_file_location("boundary_verify", HERE / "verify.py")
        verify = importlib.util.module_from_spec(vspec)
        vspec.loader.exec_module(verify)
        full = producer.make_plan()
        plan = dict(full, cases=[dict(full["cases"][0], steps=full["cases"][0]["steps"][:1])])
        base = {field: None for field in producer.BEHAVIOR}
        base.update({"logs": [], "compute_units": 1, "error": None, "accounts": []})
        receipts = [{"case": plan["cases"][0]["name"], "label": plan["cases"][0]["steps"][0]["label"],
                     "data": plan["cases"][0]["steps"][0]["data"], "original": base, "candidate": dict(base)}]
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            images = {}
            for side in ("original", "candidate"):
                images[side] = root / (side + ".so")
                images[side].write_bytes(b"elf")
            provenance = {side + "_sha256": producer.sha256(images[side]) for side in images}
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / "plan.json.gz").write_bytes(producer.gzip_bytes(producer.canonical(plan).encode()))
            (runtime / "receipts.jsonl.gz").write_bytes(
                producer.gzip_bytes((producer.canonical(receipts[0]) + "\n").encode()))
            report = producer.build_report(plan, receipts, provenance)
            (runtime / "report.json.gz").write_bytes(producer.gzip_bytes(json.dumps(report).encode()))
            argv = ["verify.py", "--images", json.dumps({k: str(v) for k, v in images.items()}),
                    "--runtime", str(runtime)]
            out = io.StringIO()
            with mock.patch.object(sys, "argv", argv), mock.patch.object(verify.producer, "run", return_value=receipts), \
                    contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as raised:
                verify.main()
            self.assertEqual(raised.exception.code, 1)
            self.assertIn("plan", out.getvalue())


if __name__ == "__main__":
    unittest.main()
