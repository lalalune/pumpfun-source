#!/usr/bin/env python3
"""A finished strict-log audit must reach a report in a new folder."""
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


class StrictOrderedLogOutputTests(unittest.TestCase):
    def test_report_parent_is_created_after_the_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            candidate.write_bytes(b"candidate")
            report = root / "report.json"
            output = root / "new" / "nested" / "strict.json"
            report.write_text(json.dumps({
                "original_sha256": gate.ORIGINAL,
                "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                "case_count": 1,
                "suites": {"case": [{"original": {"logs": ["same"]},
                                      "candidate": {"logs": ["same"]}}]},
            }), encoding="utf-8")
            argv = ["pump_strict_ordered_logs.py", "--report", str(report),
                    "--candidate", str(candidate), "--output", str(output)]
            with mock.patch.object(sys, "argv", argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    gate.main()
                except FileNotFoundError as error:
                    self.fail(f"finished audit was lost: {error}")
            self.assertEqual(json.loads(output.read_text())["case_pairs"], 1)
            self.assertEqual(list(output.parent.glob(".strict.json.*")), [])


if __name__ == "__main__":
    unittest.main()
