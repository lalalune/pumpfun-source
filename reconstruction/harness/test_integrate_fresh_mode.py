#!/usr/bin/env python3
"""Fresh-control CLI admission and fail-closed composition tests."""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate
from source_inputs import snapshot


def crate(path: Path, lib: str, extra=None) -> Path:
    (path / "src").mkdir(parents=True)
    (path / "Cargo.toml").write_text('[package]\nname="fixture"\nversion="0.0.0"\n', encoding="utf-8")
    (path / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
    (path / "src/lib.rs").write_text(lib, encoding="utf-8")
    for name, value in (extra or {}).items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    return path


class FreshModeCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="integrate-fresh-mode-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sc = self.root / "reconstruction"
        self.base = crate(self.root / "base", "pub fn base() {}\n")
        self.part = crate(
            self.root / "part",
            "pub fn base() {}\n",
            {"src/independent.rs": b"pub fn recovered() {}\n"},
        )
        self.calls = []

        def qualify(base, candidate, output, **kwargs):
            self.calls.append(
                {
                    "base": snapshot(base),
                    "candidate": snapshot(candidate),
                    "output": output,
                    "kwargs": kwargs,
                }
            )
            output.mkdir(parents=True)
            receipt = {
                "schema": "pump-fresh-control-v1",
                "qualification": {
                    "accepted": True,
                    "rejection_reasons": [],
                    "base_source_sha256": snapshot(base)["sha256"],
                    "candidate_source_sha256": snapshot(candidate)["sha256"],
                },
                "comparison": {
                    "missing": [],
                    "added": [],
                    "resized": [],
                    "normalized_gains": ["0x100"],
                    "normalized_losses": [],
                    "raw_gains": [],
                    "raw_losses": [],
                },
            }
            (output / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            return receipt

        self.patchers = [
            mock.patch.object(integrate, "SC", self.sc),
            mock.patch.object(integrate, "run_fresh_control", side_effect=qualify),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(self.patchers)])

    def argv(self, name="trial", parts=None):
        values = [
            "integrate.py",
            "--name",
            name,
            "--base-src",
            str(self.base),
            "--fresh-control",
            "--expect-base-sha256",
            snapshot(self.base)["sha256"],
        ]
        for label, source, derived in parts or [("independent", self.part, self.base)]:
            values += ["--part", f"{label}={source}", "--base-of", f"{label}={derived}"]
        return values

    def run_main(self, argv):
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            return integrate.main()

    def test_compatible_part_qualifies_against_owned_base_and_composition(self):
        code = self.run_main(self.argv())
        self.assertEqual(code, 0)
        self.assertEqual(len(self.calls), 1)
        report = json.loads((self.sc / "integ/trial/report.json").read_text())
        self.assertEqual(report["mode"], "fresh_control")
        self.assertTrue(report["qualification"]["accepted"])
        self.assertEqual(report["qualification"]["applied_parts"], ["independent"])
        self.assertEqual(report["qualification"]["rejected_parts"] if "rejected_parts" in report["qualification"] else [], [])
        self.assertNotEqual(self.calls[0]["base"]["sha256"], self.calls[0]["candidate"]["sha256"])

    def test_part_conflict_never_runs_pair_and_cannot_qualify(self):
        one = crate(self.root / "one", "pub fn base() { let _ = 1; }\n")
        two = crate(self.root / "two", "pub fn base() { let _ = 2; }\n")
        code = self.run_main(self.argv(parts=[("one", one, self.base), ("two", two, self.base)]))
        self.assertEqual(code, 1)
        self.assertEqual(self.calls, [])
        report = json.loads((self.sc / "integ/trial/report.json").read_text())
        self.assertFalse(report["qualification"]["accepted"])
        self.assertEqual(report["qualification"]["rejection_reasons"], ["part_not_applied"])
        self.assertEqual(report["qualification"]["rejected_parts"], [{"label": "two", "status": "conflict"}])

    def test_fresh_pair_rejection_controls_cli_exit(self):
        integrate.run_fresh_control.side_effect = None
        integrate.run_fresh_control.return_value = {
            "qualification": {"accepted": False, "rejection_reasons": ["raw_match_regression"]}
        }
        code = self.run_main(self.argv())
        self.assertEqual(code, 1)
        report = json.loads((self.sc / "integ/trial/report.json").read_text())
        self.assertFalse(report["qualification"]["accepted"])
        self.assertEqual(report["qualification"]["rejection_reasons"], ["raw_match_regression"])

    def test_base_digest_mismatch_fails_before_output_or_build(self):
        argv = self.argv()
        argv[argv.index("--expect-base-sha256") + 1] = "0" * 64
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            self.run_main(argv)
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.sc / "integ/trial").exists())
        self.assertEqual(self.calls, [])

    def test_fresh_mode_refuses_no_build(self):
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            self.run_main(self.argv() + ["--no-build"])
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.sc / "integ/trial").exists())

    def test_expected_base_digest_is_not_accepted_by_historical_mode(self):
        argv = [
            "integrate.py",
            "--name",
            "trial",
            "--base-src",
            str(self.base),
            "--no-build",
            "--expect-base-sha256",
            snapshot(self.base)["sha256"],
        ]
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            self.run_main(argv)
        self.assertEqual(raised.exception.code, 2)
        self.assertFalse((self.sc / "integ/trial").exists())

    def test_atomic_report_publication_preserves_previous_complete_json(self):
        output = self.root / "report.json"
        output.write_text('{"old": true}\n', encoding="utf-8")
        with mock.patch.object(integrate.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaisesRegex(OSError, "interrupted"):
                integrate.publish_report(output, {"new": True})
        self.assertEqual(output.read_text(), '{"old": true}\n')
        self.assertEqual(list(self.root.glob(".report-*")), [])


if __name__ == "__main__":
    unittest.main()
