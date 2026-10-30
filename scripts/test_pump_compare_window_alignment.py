"""Regression checks for aligned selected-window bounds in byte comparison.

Sibling of reconstruction/harness/score.py, which rejects selected windows
whose bounds are not multiples of eight: SBF instructions occupy complete
8-byte slots, and scripts/pump_compare_function_bytes.normalize asserts
exactly that. selected_window admitted an unaligned matched window instead
(for example start 4096, end 4100), so the comparison proceeded to
normalize and crashed with AssertionError instead of rejecting the
inventory row. Bounds that are not multiples of eight are now rejected at
selection, with the same invalid-bounds error as an inverted range.
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


class SelectedWindowAlignmentTests(unittest.TestCase):
    def test_unaligned_end_is_rejected(self):
        with self.assertRaises(ValueError):
            select(HEADER + "pump\tselected\t4096\t4100\n")

    def test_unaligned_start_is_rejected(self):
        with self.assertRaises(ValueError):
            select(HEADER + "pump\tselected\t4100\t4112\n", start=4100)

    def test_aligned_window_is_still_admitted(self):
        row = select(HEADER + "pump\tselected\t4096\t4104\n")
        self.assertEqual(row["original_end"], "4104")

    def test_unaligned_nonmatching_row_is_rejected(self):
        with self.assertRaises(ValueError):
            select(
                HEADER
                + "pump\tselected\t8192\t8196\n"
                + "pump\tselected\t4096\t4104\n"
            )


if __name__ == "__main__":
    unittest.main()
