#!/usr/bin/env python3
"""Window-inventory selection; no objdump, candidate build, or target execution."""
import csv
import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_existing_report_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'original.so'
            original.write_bytes(b'O')
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'C')
            objdump = root / 'llvm-objdump'
            objdump.write_bytes(b'tool')
            inventory_path = root / 'functions.tsv'
            with inventory_path.open('w', newline='') as stream:
                writer = csv.writer(stream, delimiter='\t')
                writer.writerow(('program', 'variant', 'original_start', 'original_end'))
                for start in range(1035):
                    writer.writerow(('pump', 'selected', start, start + 1))
            output = root / 'report.json'
            output.write_text('retained\n')
            sections = {'.text': {'addr': 0, 'size': 1035}}
            with patch.object(inventory, 'ORIGINAL', original), \
                    patch.object(inventory, 'EXPECTED_ORIGINAL', hashlib.sha256(b'O').hexdigest()), \
                    patch.object(inventory, 'sections', return_value=sections), \
                    patch.object(inventory, 'candidate_functions', return_value=[]), \
                    patch.object(inventory, 'function_body', return_value=b'x'), \
                    patch.object(inventory, 'window_inventory', return_value=inventory_path), \
                    patch.object(sys, 'argv', [
                        'pump_exact_body_inventory.py', '--candidate', str(candidate),
                        '--output', str(output), '--objdump', str(objdump)]):
                with self.assertRaises(FileExistsError):
                    inventory.main()
            self.assertEqual(output.read_text(), 'retained\n')


if __name__ == '__main__':
    unittest.main()
