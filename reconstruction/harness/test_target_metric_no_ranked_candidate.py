"""A window with no ranked candidate was not measured, so it cannot exit 0."""
import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

from score import BASE, original_windows  # noqa: E402
import target_metric as metric  # noqa: E402


class NoRankedCandidateTests(unittest.TestCase):
    def run_metric(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = metric.main(argv)
            except SystemExit as error:
                code = error.code
        return code, stdout.getvalue(), stderr.getvalue()

    def test_stripped_image_is_not_a_clean_measurement(self):
        start = original_windows()[0]['start']
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'rows.json'
            code, stdout, stderr = self.run_metric(
                [str(BASE / 'original.so'), hex(start), '--json', str(report)])
            self.assertEqual(code, 2)
            self.assertEqual(stdout, '')
            self.assertIn('no candidate function', stderr)
            self.assertFalse(report.exists())

    def test_batch_with_one_unmeasured_window_is_not_partial(self):
        first, second = [window['start'] for window in original_windows()[:2]]
        rows = [[{'window': hex(first)}], []]
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'rows.json'
            with patch.object(metric, 'measure_window', side_effect=rows):
                code, stdout, stderr = self.run_metric(
                    [str(BASE / 'original.so'), hex(first), hex(second), '--json', str(report)])
            self.assertEqual(code, 2)
            self.assertEqual(stdout, '')
            self.assertIn(hex(second), stderr)
            self.assertFalse(report.exists())

    def test_measured_windows_still_report(self):
        first, second = [window['start'] for window in original_windows()[:2]]
        rows = [[{'window': hex(first)}], [{'window': hex(second)}]]
        with patch.object(metric, 'measure_window', side_effect=rows):
            code, stdout, _ = self.run_metric([str(BASE / 'original.so'), hex(first), hex(second)])
        self.assertEqual(code, 0)
        self.assertEqual(len(stdout.splitlines()), 2)


if __name__ == '__main__':
    unittest.main()
