"""Roadmap instruction classes and rodata string addresses."""
import struct
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reconstruction_roadmap as roadmap


def insn(opcode, src=0, dst=0, offset=0, immediate=0):
    return struct.pack('<BBhi', opcode, (src << 4) | dst, offset, immediate)


class CallClassificationTests(unittest.TestCase):
    def test_source_nibble_distinguishes_internal_calls_from_syscalls(self):
        elf = type('Elf', (), {'relocations': {}})()
        internal = insn(0x85, src=1, immediate=4)
        relocated = insn(0x85, src=1, immediate=-1)
        syscall = insn(0x85, src=0, immediate=7)
        callx = insn(0x8d, immediate=2)
        blob = internal + relocated + syscall + callx
        self.assertEqual(
            [roadmap.classify_instruction(blob, at, elf) for at in range(0, len(blob), 8)],
            ['call_internal', 'call_relocated', 'syscall_7', 'callx'],
        )
        patterns = roadmap.analyze_window_patterns(type('Image', (), {'b': blob})(), 0, len(blob))
        self.assertEqual(patterns['calls'], 3)
        self.assertEqual(patterns['syscalls'], {'syscall_7': 1})

    def test_relocated_direct_call_is_not_an_internal_edge(self):
        blob = insn(0x85, src=1, immediate=4)
        elf = type('Elf', (), {'relocations': {0: {'type': 10}}})()
        self.assertEqual(roadmap.classify_instruction(blob, 0, elf), 'call_relocated')

    def test_captured_pump_text_has_internal_calls_and_callx(self):
        data = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        elf = type('Elf', (), {'relocations': {}})()
        counts = {}
        text = roadmap_text(data)
        offset = 0
        while offset + 8 <= len(text):
            label = roadmap.classify_instruction(text, offset, elf)
            counts[label] = counts.get(label, 0) + 1
            offset += 16 if text[offset] == 0x18 else 8
        self.assertEqual(counts.get('call_internal'), 10591)
        self.assertEqual(counts.get('call_relocated'), 270)
        self.assertEqual(counts.get('callx'), 144)
        self.assertNotIn('call_other', counts)
        self.assertNotIn('other_0x8d', counts)


def roadmap_text(blob):
    section_off, = struct.unpack_from('<Q', blob, 40)
    entsize, count, names = struct.unpack_from('<HHH', blob, 58)
    headers = [struct.unpack_from('<IIQQQQIIQQ', blob, section_off + i * entsize) for i in range(count)]
    strings = headers[names]
    def name(off):
        start = strings[4] + off
        return blob[start:blob.index(b'\0', start)].decode()
    text = next(header for header in headers if name(header[0]) == '.text')
    return blob[text[4]:text[4] + text[5]]


class RodataStringTests(unittest.TestCase):
    def test_trailing_string_uses_virtual_address(self):
        payload = b'\x00hello'
        elf = type('Elf', (), {
            'b': b'pad' + payload,
            'secs': {'.rodata': (0, 0, 0, 0x5000, 3, len(payload))},
        })()
        found = roadmap.analyze_cross_references(elf, [])
        self.assertEqual(found, {0x5001: 'hello'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
