"""Keep the official scorer and detailed comparison's narrow masking contract aligned."""
import csv
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_compare_function_bytes as detailed
import score


def insn(op, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi', op, regs, offset, immediate)


def lddw(value, regs=1):
    return struct.pack('<BBhI', 0x18, regs, 0, value & 0xffffffff) + struct.pack('<BBBBI', 0, 0, 0, 0, value >> 32)


class NormalizationConformance(unittest.TestCase):
    def setUp(self):
        self.sections = {'.text': {'addr': 4096, 'offset': 0, 'size': 256},
                         '.rodata': {'addr': 8192, 'offset': 256, 'size': 16},
                         '.high': {'addr': 0x180000000, 'offset': 272, 'size': 16}}

    def check_case(self, raw, expected):
        self.assertEqual(score.normalize(raw, 4096, self.sections), expected)
        self.assertEqual(detailed.normalize(raw, 4096, self.sections)[0], expected)

    def test_mask_only_internal_calls_and_in_section_pointers(self):
        cases = [(insn(0x85, 0x10, immediate=7), insn(0x85, 0x10)),
                 (insn(0x85, 0x10, immediate=-2), insn(0x85, 0x10))]
        for value in [4096, 4351, 8192, 8207, 0x180000005]:
            cases.append((lddw(value), lddw(0)))
        for raw, expected in cases:
            with self.subTest(raw=raw.hex()): self.check_case(raw, expected)

    def test_preserve_nonrelocation_fields_and_boundary_literals(self):
        unchanged = [insn(0x85, 0x10, immediate=-1), insn(0x85, 0, immediate=7),
                     insn(0xb7, 1, immediate=4096), insn(0x15, 1, offset=5, immediate=4096),
                     insn(0x7b, 0x1a, offset=-32), lddw(0), lddw(4095), lddw(4352), lddw(8208)]
        for raw in unchanged:
            with self.subTest(raw=raw.hex()): self.check_case(raw, raw)
        # LDDW's continuation can look like a call opcode; it is data, not an instruction.
        raw = insn(0x18, 1, immediate=12) + insn(0x85, 0x10, immediate=7)
        self.check_case(raw, raw)
        raw = insn(0x85, 0x13, offset=9, immediate=22)
        self.check_case(raw, insn(0x85, 0x13, offset=9))

    def test_truncated_instructions_are_rejected(self):
        for raw in [b'\x85', insn(0x18)]:
            for normalize in [score.normalize, detailed.normalize]:
                with self.subTest(raw=raw.hex(), tool=normalize.__module__), self.assertRaises((ValueError, struct.error, AssertionError)):
                    normalize(raw, 4096, self.sections)

    def test_all_retained_selected_pump_windows(self):
        blob = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        sections = score.sections(blob)
        count = 0
        with (ROOT / 'reconstruction/base/functions.tsv').open() as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                if row['program'] != 'pump' or row['variant'] != 'selected': continue
                start, end = int(row['original_start']), int(row['original_end'])
                raw = score.body(blob, sections, start, end - start)
                with self.subTest(start=hex(start)):
                    self.assertEqual(score.normalize(raw, start, sections), detailed.normalize(raw, start, sections)[0])
                count += 1
        self.assertEqual(count, 1035)


if __name__ == '__main__': unittest.main()
