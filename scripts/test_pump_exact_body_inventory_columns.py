#!/usr/bin/env python3
"""Regression checks for unique required columns in the exact-body inventory.

Sibling of merged #2501, which rejects ambiguous required window-inventory
columns in scripts/pump_compare_function_bytes.selected_window, and of merged
#2163 (reconstruction/harness/score.py). scripts/pump_exact_body_inventory
read the same functions.tsv inventory with a permissive DictReader, so a
duplicated required column was silently resolved by DictReader's last-wins
rule: a second program column admitted a row the first column excluded, and
a second original_start substituted a different window than the first column
described.
"""

import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pump_exact_body_inventory as inventory


def select(text):
    return inventory.selected_windows(io.StringIO(text))


class ExactBodyInventoryColumnTests(unittest.TestCase):
    def test_duplicate_program_column_is_rejected(self):
        text = (
            "program\tprogram\tvariant\toriginal_start\toriginal_end\n"
            "other\tpump\tselected\t4096\t4104\n"
        )
        with self.assertRaises(ValueError):
            select(text)

    def test_duplicate_original_start_is_rejected(self):
        text = (
            "program\tvariant\toriginal_start\toriginal_start\toriginal_end\n"
            "pump\tselected\t4096\t8192\t8208\n"
        )
        with self.assertRaises(ValueError):
            select(text)

    def test_duplicate_unrequired_column_is_still_admitted(self):
        text = (
            "program\tvariant\tnote\tnote\toriginal_start\toriginal_end\n"
            "pump\tselected\ta\tb\t4096\t4104\n"
        )
        self.assertEqual(select(text), [(4096, 4104)])

    def test_unique_required_columns_are_still_admitted(self):
        text = (
            "program\tvariant\toriginal_start\toriginal_end\n"
            "pump\tselected\t4096\t4104\n"
            "pump\tother\t4096\t4104\n"
            "other\tselected\t4096\t4104\n"
        )
        self.assertEqual(select(text), [(4096, 4104)])


if __name__ == "__main__":
    unittest.main()
