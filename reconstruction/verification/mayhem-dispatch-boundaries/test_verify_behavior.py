#!/usr/bin/env python3
"""Real LiteSVM runs: the verifier must refuse a candidate that behaves differently."""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("boundary_verify", HERE / "verify.py")
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)
producer = verify.producer
CAPTURED = ROOT / "evidence/original/mayhem/deployed.so"
OTHER_PROGRAM = ROOT / "evidence/original/pump_fees/deployed.so"


def one_step_plan():
    full = producer.make_plan()
    case = next(row for row in full["cases"] if row["name"] == "buy")
    step = next(row for row in case["steps"] if row["label"] == "recognized-disc-only")
    return dict(full, cases=[dict(case, steps=[step])])


def produce_then_verify(candidate):
    images = json.dumps({"original": str(CAPTURED), "candidate": str(candidate)})
    plan = one_step_plan()
    with tempfile.TemporaryDirectory() as directory, mock.patch.object(producer, "make_plan", return_value=plan):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(
                sys, "argv", ["producer.py", "--root", str(ROOT), "--images", images, "--out", directory]):
            producer.main()
        produced = json.loads(out.getvalue())
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), mock.patch.object(
                sys, "argv", ["verify.py", "--images", images, "--runtime", directory + "/runtime"]):
            try:
                verify.main()
            except SystemExit as stop:
                code = stop.code
    return produced, code, out.getvalue()


class BehaviorGate(unittest.TestCase):
    def test_behavior_mismatch_is_rejected(self):
        produced, code, output = produce_then_verify(OTHER_PROGRAM)
        self.assertEqual(produced["behavior_mismatches"], 1)
        self.assertEqual(code, 1, output)
        self.assertIn("behavior", output)
        self.assertNotIn('"ok": true', output)

    def test_equal_behavior_still_passes(self):
        produced, code, output = produce_then_verify(CAPTURED)
        self.assertEqual(produced["behavior_mismatches"], 0)
        self.assertEqual(code, 0, output)
        self.assertIn('"ok": true', output)


if __name__ == "__main__":
    unittest.main()
