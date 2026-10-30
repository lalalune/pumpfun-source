#!/usr/bin/env python3
"""A probe report keeps the permissions of an ordinary file under the umask."""
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe_report  # noqa: E402


class ProbeReportModeTests(unittest.TestCase):
    def published_mode(self, umask, prior=False):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "report.json"
            if prior:
                report.write_text("{}\n", encoding="utf-8")
            previous = os.umask(umask)
            try:
                probe_report.write_json_report(report, {"new": "complete"})
            finally:
                os.umask(previous)
            self.assertEqual(os.listdir(temporary), ["report.json"])
            return stat.S_IMODE(report.stat().st_mode)

    def test_new_report_follows_the_process_umask(self):
        for umask, mode in ((0o022, 0o644), (0o027, 0o640)):
            with self.subTest(umask=oct(umask)):
                self.assertEqual(oct(self.published_mode(umask)), oct(mode))

    def test_replacement_report_follows_the_process_umask(self):
        self.assertEqual(oct(self.published_mode(0o022, prior=True)), oct(0o644))


if __name__ == "__main__":
    unittest.main()
