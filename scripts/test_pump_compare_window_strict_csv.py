"""Regression checks for strict window-inventory parsing in byte comparison.

Sibling of merged #2185, which enabled strict CSV parsing in
reconstruction/harness/score.py after an unterminated quoted final bound
such as original_end="4104 at EOF was admitted by the permissive reader
(int() accepts the resulting field) and produced a successful score
receipt. scripts/pump_compare_function_bytes.selected_window used the
same permissive reader, so the same truncated record selected a window
for comparison instead of being rejected.
"""

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pump_compare_function_bytes as comparison


HEADER = "program\tvariant\toriginal_start\toriginal_end\n"


def select(text, start=4096):
    return comparison.selected_window(io.StringIO(text), start)


class SelectedWindowStrictCsvTests(unittest.TestCase):
    def test_unterminated_quoted_bound_at_eof_is_rejected(self):
        with self.assertRaises(ValueError):
            select(HEADER + 'pump\tselected\t4096\t"4104')

    def test_unterminated_quoted_bound_with_lf_is_rejected(self):
        with self.assertRaises(ValueError):
            select(HEADER + 'pump\tselected\t4096\t"4104\n')

    def test_unterminated_quoted_bound_with_crlf_is_rejected(self):
        with self.assertRaises(ValueError):
            select(HEADER + 'pump\tselected\t4096\t"4104\r\n')

    def test_properly_closed_quoted_bound_is_still_admitted(self):
        row = select(HEADER + 'pump\tselected\t4096\t"4104"\n')
        self.assertEqual(row["original_end"], "4104")

    def test_unquoted_bound_is_still_admitted(self):
        row = select(HEADER + "pump\tselected\t4096\t4104\n")
        self.assertEqual(row["original_end"], "4104")


if __name__ == "__main__":
    unittest.main()
