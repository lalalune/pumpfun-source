"""The call-sequence report must not turn an impossible original window into a zero-call result."""
import contextlib
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import callseq  # noqa: E402

CAPTURE = Path(__file__).resolve().parents[4] / 'evidence/original/pump/deployed.so'
TEXT = callseq.sections(CAPTURE.read_bytes())['.text']


def run(*arguments):
    # The capture is stripped, so one symbol stands in for the candidate's table.
    symbols = [(0x22a10, 27400, 'admin_cto7execute')]
    argv = ['callseq.py', '--cand', str(CAPTURE), '--orig-names', str(CAPTURE), *arguments]
    stdout, stderr = io.StringIO(), io.StringIO()
    with mock.patch.object(callseq, 'function_symbols', lambda blob: symbols), \
            mock.patch.object(sys, 'argv', argv), \
            contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            callseq.main()
            status = 0
        except SystemExit as stop:
            status = stop.code
        except struct.error as error:
            status = repr(error)
    return status, stdout.getvalue(), stderr.getvalue()


class WindowAdmission(unittest.TestCase):
    def test_default_window_is_compared(self):
        status, stdout, _ = run()
        self.assertEqual(status, 0)
        self.assertIn('original 0x22a10 27400 B: 157 calls', stdout)

    def test_impossible_windows_are_usage_errors(self):
        end = TEXT['addr'] + TEXT['size']
        for window, size in ((hex(end + 0x1000), '256'), ('0x8', '64'), (hex(end - 8), '16'),
                             ('0x22a10', '0'), ('0x22a10', '-8'), ('0x22a14', '64'), ('0x22a10', '12')):
            with self.subTest(window=window, size=size), tempfile.TemporaryDirectory() as temporary:
                report = Path(temporary)/'report.json'
                status, stdout, stderr = run('--window', window, '--size', size, '--json', str(report))
                self.assertEqual(status, 2, stdout[:120])
                self.assertRegex(stderr, 'outside .text|whole instructions|nonnegative')
                self.assertFalse(report.exists())


if __name__ == '__main__':
    unittest.main()
