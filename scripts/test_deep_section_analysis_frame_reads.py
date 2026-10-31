#!/usr/bin/env python3
"""Layer 4 reads through the r10 frame pointer are not deserialized structs."""
import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deep_section_analysis


def patterns(base_register, offsets):
    regs = (base_register << 4) | 1
    code = b"".join(struct.pack("<BBhi", 0x79, regs, offset, 0) for offset in offsets)
    header = bytearray(64)
    struct.pack_into("<Q", header, 24, 64)
    elf = SimpleNamespace(b=bytes(header) + code, lo=64, hi=64 + len(code),
                          entries=[64], funcs=[], secs={})
    return deep_section_analysis.recover_anchor_idl(elf)["deserialization_patterns"]


class FrameReadTests(unittest.TestCase):
    def test_frame_pointer_reads_are_not_reported(self):
        self.assertEqual(patterns(10, [-40, -32, -24, -16]), [])

    def test_other_bases_keep_their_negative_offsets(self):
        rows = patterns(2, [-16, -8, 0])
        self.assertEqual([row["base_reg"] for row in rows], [2])
        self.assertEqual(rows[0]["field_offsets"], [-16, -8, 0])
        self.assertEqual(rows[0]["likely_struct_size"], 8)


if __name__ == "__main__":
    unittest.main()
