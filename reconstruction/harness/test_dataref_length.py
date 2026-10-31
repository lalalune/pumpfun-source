"""Data-reference auditing must preserve the requested comparison extent."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / 'evidence/original/pump/deployed.so'
AUDIT = ROOT / 'reconstruction/pump-main/lanes/callgraph-census/dataref_audit.py'


def symbolized(blob, start, size):
    """Give a disposable capture copy one function symbol, preserving its code."""
    output = bytearray(blob)
    shoff = struct.unpack_from('<Q', output, 40)[0]
    count, names_index = struct.unpack_from('<HH', output, 60)
    headers = [list(struct.unpack_from('<IIQQQQIIQQ', output, shoff + i * 64)) for i in range(count)]
    names_header = headers[names_index]
    names = output[names_header[4]:names_header[4] + names_header[5]]
    str_name = len(names)
    sym_name = str_name + len(b'.strtab\0')
    names.extend(b'.strtab\0.symtab\0')
    names_header[4], names_header[5] = len(output), len(names)
    output.extend(names)
    strings = b'\0captured_window\0'
    headers.append([str_name, 3, 0, 0, len(output), len(strings), 0, 0, 1, 0])
    output.extend(strings)
    output.extend(bytes(-len(output) % 8))
    text_index = next(i for i, h in enumerate(headers) if names[h[0]:].split(b'\0', 1)[0] == b'.text')
    symbols = bytes(24) + struct.pack('<IBBHQQ', 1, 0x12, 0, text_index, start, size)
    headers.append([sym_name, 2, 0, 0, len(output), len(symbols), count, 1, 8, 24])
    output.extend(symbols)
    new_shoff = len(output)
    for header in headers:
        output.extend(struct.pack('<IIQQQQIIQQ', *header))
    struct.pack_into('<Q', output, 40, new_shoff)
    struct.pack_into('<H', output, 60, len(headers))
    return output


class DatarefLengthTests(unittest.TestCase):
    def audit(self, start, size, changed_offset=None, *, edit=None, width=16):
        original = CAPTURE.read_bytes()
        candidate = symbolized(original, start, size)
        if changed_offset is not None:
            candidate[changed_offset] ^= 1
        if edit is not None:
            edit(candidate)
        with tempfile.TemporaryDirectory(prefix='pump-dataref-length-') as directory:
            path = Path(directory) / 'candidate.so'
            report = Path(directory) / 'report.json'
            path.write_bytes(candidate)
            result = subprocess.run([sys.executable, '-B', str(AUDIT), '--cand', str(path), '--json', str(report),
                                     '--width', str(width)],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = json.loads(report.read_text())
        self.assertEqual(hashlib.sha256(CAPTURE.read_bytes()).digest(), hashlib.sha256(original).digest())
        return output

    def test_unrelated_scalar_after_call_does_not_hide_data_changes(self):
        # The retained 0x132510 window loads the 32-byte value into r3 at
        # offset 0x158, calls at offset 0x170, then sets unrelated r1 = 2.
        # This is not a two-byte string. All code bytes remain unchanged.
        for offset in (None, 0, 2, 15):
            with self.subTest(changed_byte=offset):
                result = self.audit(0x132510, 520, None if offset is None else 0x1b79df + offset)
                self.assertEqual((result['clean'], result['flagged']), (1, 0) if offset is None else (0, 1))
                if offset is not None:
                    difference = result['rows'][0]['candidates'][0]['bad'][0]
                    self.assertEqual(difference['off'], '0x158')
                    self.assertEqual(len(bytes.fromhex(difference['orig_bytes'])), 16)

    def test_adjacent_short_string_length_remains_respected(self):
        # Retained 0xa8f0 loads "()" into r2 and immediately sets r3 = 2.
        # A byte outside that string must not introduce a neighbouring-data flag.
        for offset in (0, 2):
            with self.subTest(changed_byte=offset):
                result = self.audit(0xa8f0, 48, 0x1b5fa2 + offset)
                self.assertEqual((result['clean'], result['flagged']), (0, 1) if offset == 0 else (1, 0))

    def test_short_section_read_does_not_hide_missing_bytes(self):
        from score import sections
        original = CAPTURE.read_bytes()
        rodata = sections(original)['.rodata']
        for available, different, width in ((16, False, 16), (1, False, 16),
                                            (1, True, 16), (1, False, 1)):
            with self.subTest(available=available, different=different, width=width):
                def edit(candidate):
                    # Relocate the captured log string to the end of .rodata in
                    # this disposable candidate. Normalized code still matches.
                    offset = rodata['offset'] + rodata['size'] - available
                    address = rodata['addr'] + rodata['size'] - available
                    candidate[offset:offset + available] = original[0x1b7b37:0x1b7b37 + available]
                    if different:
                        candidate[offset] ^= 1
                    struct.pack_into('<I', candidate, 0x120584, address)
                result = self.audit(0x120580, 40, edit=edit, width=width)
                mismatch = different or available < width
                self.assertEqual((result['clean'], result['flagged']), (0, 1) if mismatch else (1, 0))
                if mismatch:
                    difference = result['rows'][0]['candidates'][0]['bad'][0]
                    self.assertEqual(len(bytes.fromhex(difference['orig_bytes'])), width)
                    self.assertEqual(len(bytes.fromhex(difference['our_bytes'])), available)


if __name__ == '__main__':
    unittest.main()
