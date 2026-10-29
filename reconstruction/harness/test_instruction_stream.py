"""Diagnostic n-grams and call counts must use logical instruction boundaries."""
from collections import Counter
import struct
import unittest

from instruction_stream import instruction_offsets
import target_metric
import win


def instruction(op, regs=0, imm=0):
    return struct.pack('<BBhi', op, regs, 0, imm)


class InstructionBoundaryTests(unittest.TestCase):
    def test_lddw_contributes_one_opcode(self):
        raw = instruction(0x18) + bytes(8) + instruction(0x07) + instruction(0x95)
        self.assertEqual(list(instruction_offsets(raw)), [0, 16, 24])
        self.assertEqual(win.opgrams(raw), Counter({(0x18, 0x07, 0x95): 1}))

    def test_constants_do_not_change_opcode_metric(self):
        prefix = instruction(0x18)
        suffix = instruction(0x07) + instruction(0x95)
        a = prefix + struct.pack('<II', 0, 123) + suffix
        b = prefix + struct.pack('<II', 0, 98765) + suffix
        self.assertEqual(win.opgrams(a), win.opgrams(b))
        self.assertEqual(sum(win.opgrams(a).values()), 1)

    def test_calls_follow_logical_boundaries(self):
        raw = (instruction(0x18) + bytes(8) + instruction(0x85, 0x10, 3)
               + instruction(0x85, 0, 123) + instruction(0x85, 0x10, -1)
               + instruction(0x95))
        self.assertEqual(target_metric.calls(raw), (1, 2))
        self.assertEqual(win.opgrams(raw, 1), Counter({(0x18,): 1, (0x85,): 3, (0x95,): 1}))

    def test_truncation_is_not_a_complete_metric(self):
        for raw in (b'\x85', instruction(0x18), instruction(0x95) + b'\x18'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                win.opgrams(raw)
            with self.subTest(calls=raw), self.assertRaises(ValueError):
                target_metric.calls(raw)

    def test_empty_and_short_ngrams(self):
        self.assertEqual(win.opgrams(b''), Counter())
        self.assertEqual(target_metric.calls(b''), (0, 0))
        self.assertEqual(win.opgrams(instruction(0x95)), Counter())

    def test_captured_text_agrees_with_existing_decoder(self):
        section = win.ORIG_SECS['.text']
        raw = win.ORIG[section['offset']:section['offset'] + section['size']]
        decoded = win.insns(raw, section['addr'], win.ORIG_SECS)
        expected = Counter(tuple(row[1][0] for row in decoded[i:i + 3])
                           for i in range(len(decoded) - 2))
        self.assertEqual(win.opgrams(raw), expected)
        self.assertLess(len(decoded), len(raw) // 8)  # fixture contains LDDW
        self.assertEqual(sum(expected.values()), len(decoded) - 2)


if __name__ == '__main__':
    unittest.main()
