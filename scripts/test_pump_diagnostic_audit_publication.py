#!/usr/bin/env python3
"""Do not publish a diagnostic audit after its source report changes."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_diagnostic_audit as gate  # noqa: E402


class DiagnosticAuditPublicationTests(unittest.TestCase):
    def test_failed_staging_leaves_no_report_or_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / "report.json"
            output = root / "audit.json"
            report.write_text(json.dumps({"suites": {"case": [{
                "original": {"logs": ["before"]},
                "candidate": {"logs": ["before"]},
            }]}}), encoding="utf-8")
            with mock.patch.object(gate.os, "fsync", side_effect=OSError("staging failed")), \
                    mock.patch.object(sys, "argv", ["pump_diagnostic_audit.py",
                        "--report", str(report), "--output", str(output)]):
                with self.assertRaisesRegex(OSError, "staging failed"):
                    gate.main()
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])

    def test_input_change_during_audit_leaves_no_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "report.json"
            output = root / "audit.json"

            def document(message):
                return {"suites": {"case": [{
                    "original": {"logs": [message]},
                    "candidate": {"logs": [message]},
                }]}}

            report_path.write_text(json.dumps(document("before")), encoding="utf-8")
            original_audit = gate.audit

            def mutate_during_audit(*args, **kwargs):
                result = original_audit(*args, **kwargs)
                report_path.write_text(
                    json.dumps(document("changed during audit")), encoding="utf-8")
                return result

            with mock.patch.object(gate, "audit", mutate_during_audit), \
                    mock.patch.object(sys, "argv", [
                        "pump_diagnostic_audit.py",
                        "--report", str(report_path),
                        "--output", str(output),
                    ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "source report changed during audit"):
                    gate.main()

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])

    def test_bound_input_keys_are_posix_on_every_host(self):
        # The bound_* receipt keys used by the differentials and the parallel
        # driver used str(Path), which spells separators per host; identical
        # inputs then hashed to different key sets on Windows than on the
        # Linux CI.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nested = root / "evidence" / "original" / "pump" / "deployed.so"
            nested.parent.mkdir(parents=True)
            nested.write_bytes(b"elf")
            external = root / "external-candidate.so"
            external.write_bytes(b"cand")
            self.assertEqual(
                gate.bound_input_key(nested, root),
                "evidence/original/pump/deployed.so")
            self.assertEqual(
                gate.bound_input_key(external, Path(temporary) / "elsewhere"),
                external.resolve().as_posix())


if __name__ == "__main__":
    unittest.main()
