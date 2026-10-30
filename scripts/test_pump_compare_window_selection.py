"""Window-selection checks for Pump function byte comparisons."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pump_compare_function_bytes as comparison
from pump_quote_control_function_match import sections


class WindowSelectionTests(unittest.TestCase):
    def setUp(self):
        self.original = comparison.ROOT / 'evidence/original/pump/deployed.so'
        self.start = sections(self.original.read_bytes())['.text']['addr']

    def run_comparison(self, rows, requested_start):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventory = root / 'functions.tsv'
            inventory.write_text(
                'program\tvariant\toriginal_start\toriginal_end\n'
                + ''.join(rows),
                encoding='utf-8',
            )
            output = root / 'comparison.json'
            argv = [
                str(Path(comparison.__file__)),
                '--original-start',
                hex(requested_start),
                '--candidate',
                str(self.original),
                '--symbol',
                'candidate',
                '--output',
                str(output),
            ]
            stderr = io.StringIO()
            with (
                mock.patch.object(comparison, 'window_inventory', return_value=inventory),
                mock.patch.object(
                    comparison,
                    'candidate_functions',
                    return_value=[(self.start, 16, 'candidate')],
                ),
                mock.patch.object(sys, 'argv', argv),
                contextlib.redirect_stderr(stderr),
            ):
                with self.assertRaises(SystemExit) as raised:
                    comparison.main()
            return raised.exception.code, stderr.getvalue(), output

    def test_unknown_window_is_a_cli_error(self):
        rows = [f'pump\tselected\t{self.start}\t{self.start + 16}\n']
        code, stderr, output = self.run_comparison(rows, self.start + 16)

        self.assertEqual(code, 2)
        self.assertIn('no selected Pump window', stderr)
        self.assertFalse(output.exists())

    def test_duplicate_window_is_rejected_as_ambiguous(self):
        rows = [
            f'pump\tselected\t{self.start}\t{self.start + 16}\n',
            f'pump\tselected\t{self.start}\t{self.start + 24}\n',
        ]
        code, stderr, output = self.run_comparison(rows, self.start)

        self.assertEqual(code, 2)
        self.assertIn('ambiguous selected Pump window', stderr)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
