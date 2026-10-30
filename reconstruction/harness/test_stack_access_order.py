import struct
import unittest
from stack_access import compare


def ins(op, regs=0, off=0, imm=0):
    return struct.pack('<BBhi', op, regs, off, imm)


class StackOrderTests(unittest.TestCase):
    def test_reorder_with_equal_counts(self):
        a, b = ins(0x79, 0xa1, -8), ins(0x7b, 0x1a, -16)
        report = compare(a+b, b+a)
        self.assertEqual(report['differences'], [])
        self.assertFalse(report['decoded_access_sequence_equal'])
        self.assertTrue(report['sequence_edits'])

    def test_inserted_spill_has_instruction_location(self):
        a, b = ins(0x79, 0xa1, -8), ins(0x7b, 0x1a, -16)
        edits = compare(a, a+b)['sequence_edits']
        self.assertEqual(edits[0]['kind'], 'insert')
        self.assertEqual(edits[0]['candidate'][0]['instruction_offset'], 8)

    def test_non_stack_and_lddw_payload_ignored(self):
        a = ins(0x79, 0xa1, -8)
        lddw = ins(0x18) + ins(0x7b, 0x1a, -16)
        self.assertTrue(compare(a, lddw+a)['decoded_access_sequence_equal'])

    def test_unknown_operations_remain_visible(self):
        report = compare(b'', ins(0xdb, 0x1a, -8))
        self.assertTrue(report['decoded_access_sequence_equal'])
        self.assertEqual(len(report['candidate']['unclassified_direct_stack_operations']), 1)
