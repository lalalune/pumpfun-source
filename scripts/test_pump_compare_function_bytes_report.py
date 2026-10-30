#!/usr/bin/env python3
"""A failed byte-comparison report write must retain the previous report."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
import pump_compare_function_bytes as tool  # noqa: E402


# Runs the real main() on the captured image; only objdump symbol reading is
# replaced, because the test needs no toolchain.
PROGRAM = textwrap.dedent("""
    import resource
    import signal
    import sys
    sys.path.insert(0, sys.argv[1])
    import pump_compare_function_bytes as tool
    start, size, limit = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    tool.candidate_functions = lambda *args, **kwargs: [(start, size, 'window')]
    sys.argv = ['tool', '--original-start', str(start), '--symbol', 'window',
                '--objdump', 'not-executed', '--candidate', sys.argv[5],
                '--output', sys.argv[6]]
    if limit:
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    tool.main()
""")


def first_selected_window():
    with tool.window_inventory().open() as stream:
        for row in csv.DictReader(stream, delimiter='\t'):
            if row['program'] == 'pump' and row['variant'] == 'selected':
                start = int(row['original_start'])
                return start, int(row['original_end']) - start
    raise AssertionError('no selected Pump window')


def run(candidate, report, limit):
    start, size = first_selected_window()
    return subprocess.run(
        [sys.executable, '-B', '-c', PROGRAM, str(SCRIPTS), str(start),
         str(size), str(limit), str(candidate), str(report)],
        capture_output=True, text=True)


@unittest.skipUnless(os.name == 'posix', 'RLIMIT_FSIZE requires POSIX')
class CompareReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.candidate = self.folder / 'candidate.so'
        self.candidate.write_bytes(
            (ROOT / 'evidence/original/pump/deployed.so').read_bytes())
        self.report = self.folder / 'report.json'

    def test_failed_write_preserves_prior_report(self):
        prior = '{"prior": "complete"}\n'
        self.report.write_text(prior, encoding='utf-8')

        completed = run(self.candidate, self.report, 64)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('File too large', completed.stderr)
        self.assertEqual(self.report.read_text(encoding='utf-8'), prior)
        self.assertEqual(list(self.folder.glob('.report.json.*')), [])

    def test_success_replaces_report_and_creates_parent(self):
        nested = self.folder / 'new' / 'report.json'

        completed = run(self.candidate, nested, 0)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(nested.read_text(encoding='utf-8'))
        self.assertTrue(report['candidates'][0]['raw_equal'])
        mask = os.umask(0)
        os.umask(mask)
        self.assertEqual(nested.stat().st_mode & 0o777, 0o666 & ~mask)


if __name__ == '__main__':
    unittest.main()
