#!/usr/bin/env python3
"""A direct curve patch must land at the offset its case names."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_creator_migration_differential as migration


def tail_case(name):
    return next(row for row in migration.cases() if row['name'] == name)


def curve_bytes(result, phase):
    return bytes.fromhex(result[phase][str(migration.CURVE)]['data'])


class DirectPatchOffsets(unittest.TestCase):
    def test_extended_tail_is_written_past_the_captured_curve(self):
        result = migration.run(tail_case('preserve-extended-tail'))
        before = curve_bytes(result, 'before')
        self.assertEqual(len(before), 266)
        self.assertEqual(before[250:], bytes([0xcd]) * 16)
        self.assertEqual(before[200:250], bytes(50))
        self.assertIsNone(result['error'])
        self.assertEqual(curve_bytes(result, 'after')[250:], bytes([0xcd]) * 16)

    def test_existing_tail_keeps_its_offset(self):
        result = migration.run(tail_case('preserve-existing-tail'))
        before = curve_bytes(result, 'before')
        self.assertEqual(len(before), 216)
        self.assertEqual(before[200:], bytes([0xab]) * 16)
        self.assertIsNone(result['error'])


if __name__ == '__main__':
    unittest.main()
