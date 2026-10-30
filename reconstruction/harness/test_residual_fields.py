import struct
import unittest
from target_metric import field_differences


def ins(op=0xb7, regs=1, off=0, imm=0):
    return struct.pack('<BBhi', op, regs, off, imm)


class ResidualFieldsTests(unittest.TestCase):
    def test_register_offset_and_immediate(self):
        r = field_differences(ins(), ins(regs=0x23, off=-2, imm=9))
        self.assertEqual(r['field_counts'], dict(displacement=1, dst=1, immediate=1, src=1))

    def test_lddw_high_word(self):
        r = field_differences(ins(0x18)+ins(0, 0), ins(0x18)+ins(0, 0, imm=1))
        self.assertEqual(r['field_counts'], {'immediate': 1})
        self.assertEqual(r['first_differences'][0]['fields']['immediate']['candidate'], 1 << 32)

    def test_boundary_change_is_not_field_comparison(self):
        self.assertFalse(field_differences(ins(0x18)+ins(0), ins()+ins())['comparable'])
        self.assertFalse(field_differences(ins(), ins()+ins())['comparable'])

    def test_limit_does_not_truncate_counts(self):
        r = field_differences(ins()*3, ins(imm=2)*3, 1)
        self.assertEqual(r['field_counts'], {'immediate': 3})
        self.assertEqual(len(r['first_differences']), 1)
        self.assertEqual(field_differences(ins(), ins(), 0)['field_counts'], {})

    def test_reserved_continuation_visible(self):
        r = field_differences(ins(0x18)+ins(0, 0), ins(0x18)+ins(0, 1))
        self.assertEqual(r['field_counts'], {'lddw_reserved': 1})
