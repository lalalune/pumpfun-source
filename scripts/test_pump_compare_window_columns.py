"""Regression checks for unique required columns in byte-comparison inventory.

Sibling of merged #2163, which rejects ambiguous required window-inventory
columns in reconstruction/harness/score.py. scripts/pump_compare_function_bytes.
selected_window only required the columns to be present, so a duplicated
required column was silently resolved by DictReader's last-wins rule: a
second original_start selected a different window than the first column
described, and a second original_end silently changed the window size.
"""

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pump_compare_function_bytes as comparison


def select(text, start):
    return comparison.selected_window(io.StringIO(text), start)


class SelectedWindowColumnTests(unittest.TestCase):
    def test_duplicate_original_start_is_rejected(self):
        text = (
            "program\tvariant\toriginal_start\toriginal_start\toriginal_end\n"
            "pump\tselected\t4096\t8192\t8208\n"
        )
        with self.assertRaises(ValueError):
            select(text, 8192)

    def test_duplicate_original_end_is_rejected(self):
        text = (
            "program\tvariant\toriginal_start\toriginal_end\toriginal_end\n"
            "pump\tselected\t4096\t4104\t4112\n"
        )
        with self.assertRaises(ValueError):
            select(text, 4096)

    def test_duplicate_unrequired_column_is_still_admitted(self):
        text = (
            "program\tvariant\tnote\tnote\toriginal_start\toriginal_end\n"
            "pump\tselected\ta\tb\t4096\t4104\n"
        )
        row = select(text, 4096)
        self.assertEqual(row["original_end"], "4104")

    def test_unique_required_columns_are_still_admitted(self):
        text = "program\tvariant\toriginal_start\toriginal_end\npump\tselected\t4096\t4104\n"
        row = select(text, 4096)
        self.assertEqual(row["original_end"], "4104")


if __name__ == "__main__":
    unittest.main()
