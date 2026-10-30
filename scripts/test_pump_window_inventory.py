#!/usr/bin/env python3
"""Window-inventory selection; no objdump, candidate build, or target execution."""
import csv
import struct
import tempfile
import unittest
from pathlib import Path

import pump_exact_body_inventory as inventory


class WindowInventoryTests(unittest.TestCase):
    def test_archived_table_wins_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archived = root / inventory.ARCHIVED_WINDOWS
            checked_in = root / inventory.CHECKED_IN_WINDOWS
            archived.parent.mkdir(parents=True)
            checked_in.parent.mkdir(parents=True)
            archived.write_text('archived\n')
            checked_in.write_text('checked-in\n')
            self.assertEqual(inventory.window_inventory(root), archived)

    def test_checked_in_table_is_used_when_the_archive_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checked_in = root / inventory.CHECKED_IN_WINDOWS
            checked_in.parent.mkdir(parents=True)
            checked_in.write_text('checked-in\n')
            self.assertEqual(inventory.window_inventory(root), checked_in)

    def test_missing_tables_are_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                inventory.window_inventory(tmp)

    def test_live_inventory_covers_captured_pump_text(self):
        path = inventory.window_inventory()
        self.assertEqual(path, inventory.ROOT / inventory.CHECKED_IN_WINDOWS)
        self.assertFalse((inventory.ROOT / inventory.ARCHIVED_WINDOWS).is_file())
        image = (inventory.ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        table = struct.unpack_from('<Q', image, 0x28)[0]
        size, count, names_index = struct.unpack_from('<HHH', image, 0x3a)
        rows = [struct.unpack_from('<IIQQQQIIQQ', image, table + i * size) for i in range(count)]
        names = image[rows[names_index][4]:rows[names_index][4] + rows[names_index][5]]
        text = next(row for row in rows if names[row[0]:].split(b'\0', 1)[0] == b'.text')
        selected = []
        with path.open() as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                if row['program'] == 'pump' and row['variant'] == 'selected':
                    selected.append((int(row['original_start']), int(row['original_end'])))
        self.assertEqual(len(selected), 1035)
        self.assertEqual(selected[0][0], text[3])
        self.assertEqual(selected[-1][1], text[3] + text[5])
        self.assertTrue(all(left[1] == right[0] for left, right in zip(selected, selected[1:])))


if __name__ == '__main__':
    unittest.main()
