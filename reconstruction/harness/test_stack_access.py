import struct
import unittest
from stack_access import accesses, compare


def instruction(op, regs, offset=0): return struct.pack('<BBhi', op, regs, offset, 0)


class StackAccessTests(unittest.TestCase):
    def test_read_write_widths_and_overlapping_ranges(self):
        report = accesses(instruction(0x79, 0xa1, -16) + instruction(0x62, 0x0a, -12) + instruction(0x73, 0x2a, -9))
        self.assertEqual([(r['offset'], r['width'], r['kind']) for r in report['accesses']],
                         [(-16, 8, 'read'), (-12, 4, 'write'), (-9, 1, 'write')])

    def test_shifts_and_added_spills_remain_visible(self):
        original = instruction(0x7b, 0x1a, -8)
        candidate = instruction(0x7b, 0x1a, -16) * 2
        changes = compare(original, candidate)['differences']
        self.assertEqual([(r['offset'], r['original_count'], r['candidate_count']) for r in changes], [(-16, 0, 2), (-8, 1, 0)])
        self.assertEqual(compare(original, original)['differences'], [])

    def test_continuation_and_nonstack_memory_are_not_counted(self):
        raw = instruction(0x18, 1) + instruction(0x7b, 0x1a, -8) + instruction(0x79, 0x12)
        self.assertEqual(accesses(raw)['accesses'], [])
        self.assertEqual(len(accesses(instruction(0xdb, 0x1a, -8))['unclassified_direct_stack_operations']), 1)

    def test_truncation_rejected(self):
        for raw in [b'\x79', instruction(0x18, 1)]:
            with self.assertRaises(ValueError): accesses(raw)


if __name__ == '__main__': unittest.main()
