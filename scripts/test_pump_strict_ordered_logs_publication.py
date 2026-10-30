#!/usr/bin/env python3
"""Do not publish a strict-log audit after its source report changes."""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_strict_ordered_logs as gate  # noqa: E402


class StrictOrderedLogPublicationTests(unittest.TestCase):
    def test_failed_staging_leaves_no_report_or_temporary_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            candidate.write_bytes(b"candidate")
            report = root / "report.json"
            output = root / "audit.json"
            report.write_text(json.dumps({
                "original_sha256": gate.ORIGINAL,
                "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                "case_count": 1,
                "suites": {"case": [{"original": {"logs": ["before"]},
                                      "candidate": {"logs": ["before"]}}]},
            }), encoding="utf-8")
            with mock.patch.object(gate.os, "fsync", side_effect=OSError("staging failed")), \
                    mock.patch.object(sys, "argv", ["pump_strict_ordered_logs.py",
                        "--report", str(report), "--candidate", str(candidate),
                        "--output", str(output)]):
                with self.assertRaisesRegex(OSError, "staging failed"):
                    gate.main()
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])

    def test_input_change_during_audit_leaves_no_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            candidate.write_bytes(b"candidate")
            report_path = root / "report.json"
            output = root / "audit.json"

            def document(marker):
                return {
                    "original_sha256": gate.ORIGINAL,
                    "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                    "case_count": 1,
                    "suites": {"case": [{
                        "original": {"logs": [marker]},
                        "candidate": {"logs": [marker]},
                    }]},
                }

            report_path.write_text(json.dumps(document("before")), encoding="utf-8")
            original_audit = gate.audit

            def mutate_during_audit(*args, **kwargs):
                result = original_audit(*args, **kwargs)
                report_path.write_text(
                    json.dumps(document("changed during audit")), encoding="utf-8")
                return result

            with mock.patch.object(gate, "audit", mutate_during_audit), \
                    mock.patch.object(sys, "argv", [
                        "pump_strict_ordered_logs.py",
                        "--report", str(report_path),
                        "--candidate", str(candidate),
                        "--output", str(output),
                    ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "Input changed during audit"):
                    gate.main()

            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".audit.json.*")), [])


if __name__ == "__main__":
    unittest.main()
