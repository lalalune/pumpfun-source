#!/usr/bin/env python3
"""Scorer function bodies must contain complete aligned instruction slots.

score.body sliced any byte range inside .text, so a symbol or inventory row whose
size was not a multiple of eight produced a body that normalize() could not
decode: the 8-byte unpack read a partial slot or ran off the range and raised
struct.error instead of naming the range. SBF instructions occupy 8-byte slots,
and the siblings that decode the same bytes (function_body in
pump_quote_control_function_match.py, elf_symbols.function_symbols) already
refuse such ranges.
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import score  # noqa: E402

IMAGE = bytes(64)
SECS = {'.text': {'addr': 0x1000, 'offset': 0, 'size': 64}}


class ScoreBodySlotTests(unittest.TestCase):
    def test_aligned_range_is_returned(self):
        self.assertEqual(score.body(IMAGE, SECS, 0x1000, 16), bytes(16))
        self.assertEqual(score.body(IMAGE, SECS, 0x1008, 8), bytes(8))

    def test_partial_slot_size_is_refused(self):
        for size in (4, 12, 20):
            with self.subTest(size=size):
                with self.assertRaisesRegex(ValueError, 'complete aligned instruction slots'):
                    score.body(IMAGE, SECS, 0x1000, size)

    def test_unaligned_address_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'complete aligned instruction slots'):
            score.body(IMAGE, SECS, 0x1004, 8)

    def test_out_of_range_keeps_its_message(self):
        with self.assertRaisesRegex(ValueError, 'outside .text'):
            score.body(IMAGE, SECS, 0x1000, 72)


if __name__ == '__main__':
    unittest.main()
