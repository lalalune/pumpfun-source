#!/usr/bin/env python3
"""A failed probe report write must retain the previous complete report."""
import subprocess
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import probe_report  # noqa: E402


class ProbeReportAtomicityTests(unittest.TestCase):
    def test_failed_replacement_preserves_prior_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.json"
            prior = b'{"prior": "complete"}\n'
            report.write_bytes(prior)
            with mock.patch.object(probe_report.os, "replace",
                                   side_effect=OSError("replacement failed")):
                with self.assertRaisesRegex(OSError, "replacement failed"):
                    probe_report.write_json_report(report, {"new": "complete"})
            self.assertEqual(report.read_bytes(), prior)
            self.assertEqual(list(report.parent.glob(".report.json.*")), [])

    @unittest.skipUnless(os.name == "posix", "RLIMIT_FSIZE requires POSIX")
    def test_file_size_failure_preserves_prior_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.json"
            prior = '{"prior": "complete"}\n'
            report.write_text(prior, encoding="utf-8")
            program = textwrap.dedent(f"""
                import resource
                import signal
                import sys
                sys.path.insert(0, {str(SCRIPTS)!r})
                from probe_report import write_json_report
                resource.setrlimit(resource.RLIMIT_FSIZE, (4096, 4096))
                signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
                write_json_report(sys.argv[1], {{"new": "x" * 200000}})
            """)

            completed = subprocess.run(
                [sys.executable, "-B", "-c", program, str(report)],
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("File too large", completed.stderr)
            self.assertEqual(report.read_text(encoding="utf-8"), prior)
            self.assertEqual(list(report.parent.glob(".report.json.*")), [])


if __name__ == "__main__":
    unittest.main()
