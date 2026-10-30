#!/usr/bin/env python3
"""Regression tests for durable local probe report output."""
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))
from probe_report import write_json_report


class ProbeReportTests(unittest.TestCase):
    def test_writes_into_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "new" / "nested" / "report.json"
            value = {"case": "clean checkout", "runs": [1, 2, 3]}

            write_json_report(report, value)

            self.assertEqual(json.loads(report.read_text(encoding="utf-8")), value)
            self.assertTrue(report.read_text(encoding="utf-8").endswith("\n"))

    def test_rewrites_an_existing_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.json"
            report.write_text("old\n", encoding="utf-8")

            write_json_report(report, {"current": True})

            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8")), {"current": True}
            )


if __name__ == "__main__":
    unittest.main()
