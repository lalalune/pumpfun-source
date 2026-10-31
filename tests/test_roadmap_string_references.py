"""Actual roadmap CLI must retain pointers inside captured printable runs."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reconstruction_roadmap as roadmap
from window_elf_reader import Elf


def captured_preview(elf, pointer):
    """Independent byte-level oracle; a preview is not a Rust string length."""
    section = elf.secs['.rodata']
    address, offset, size = section[3:6]
    raw = elf.b[offset:offset + size]
    index = pointer - address
    if not 0 <= index < len(raw) or not 32 <= raw[index] < 127:
        return None
    start, end = index, index + 1
    while start > 0 and 32 <= raw[start - 1] < 127:
        start -= 1
    while end < len(raw) and 32 <= raw[end] < 127:
        end += 1
    if end - start < 4:
        return None
    return raw[index:min(end, index + 80)].decode('ascii')


class RoadmapStringReferencesTests(unittest.TestCase):
    def test_actual_cli_retains_captured_string_suffixes(self):
        with tempfile.TemporaryDirectory(prefix='roadmap-strings-') as temporary:
            output = Path(temporary) / 'packet'
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts/reconstruction_roadmap.py'),
                 '--output', str(output)], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for program in ('pump', 'pump_amm', 'mayhem'):
                elf = Elf(ROOT / f'evidence/original/{program}/deployed.so')
                details = json.loads((output / f'{program}-details.json').read_text(encoding='utf-8'))
                references = []
                for at, relocation in elf.relocations.items():
                    if relocation['type'] == 8 and elf.b[at] == 0x18:
                        low = struct.unpack_from('<I', elf.b, at + 4)[0]
                        high = struct.unpack_from('<I', elf.b, at + 12)[0]
                        preview = captured_preview(elf, low | (high << 32))
                        if preview is not None:
                            references.append((at, preview))
                self.assertTrue(references, program)
                for window in details['window_details']:
                    start = window['address_decimal']
                    expected = [text for at, text in references
                                if start <= at < start + window['size']][:10]
                    self.assertEqual(window['string_references'], expected,
                                     (program, window['address']))
                if program == 'pump':
                    window = next(w for w in details['window_details']
                                  if w['address_decimal'] == 0x120580)
                    self.assertTrue(window['string_references'][0].startswith(
                        'Instruction: IdlCloseAccount'))

    def test_preview_stays_inside_printable_run(self):
        elf = Elf(ROOT / 'evidence/original/pump/deployed.so')
        strings = roadmap.analyze_cross_references(elf, elf.entries)
        starts = sorted(strings)
        start = starts[0]
        text = strings[start]
        preview = roadmap.rodata_string_preview
        self.assertIsNone(preview(strings, starts, start - 1))
        self.assertEqual(preview(strings, starts, start), text[:80])
        self.assertEqual(preview(strings, starts, start + len(text) - 1), text[-1:])
        self.assertIsNone(preview(strings, starts, start + len(text)))
        self.assertIsNone(preview({}, [], start))
        self.assertEqual(preview(strings, starts, 0x1b7b37),
                         captured_preview(elf, 0x1b7b37))


if __name__ == '__main__':
    unittest.main(verbosity=2)
