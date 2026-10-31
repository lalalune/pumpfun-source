import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import target_metric


class MetricInputErrorsTests(unittest.TestCase):
    def assert_invalid(self, candidate, report):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit) as raised:
                target_metric.main([str(candidate), '0', '--json', str(report)])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('error:', err.getvalue())
        self.assertFalse(report.exists())

    def test_missing_and_malformed_candidate_leave_no_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            with patch.object(target_metric, 'original_windows', return_value=[{'start': 0}]):
                self.assert_invalid(candidate, root / 'missing.json')
                for blob in (b'', b'not an ELF', b'\x7fELF' + bytes(60)):
                    with self.subTest(blob=blob):
                        candidate.write_bytes(blob)
                        self.assert_invalid(candidate, root / 'invalid.json')

    def test_inventory_read_error_is_a_cli_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(target_metric, 'original_windows', side_effect=OSError('unreadable inventory')):
                self.assert_invalid(root / 'candidate.so', root / 'report.json')


if __name__ == '__main__':
    unittest.main()
