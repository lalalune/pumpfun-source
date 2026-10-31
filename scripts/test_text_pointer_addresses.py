"""Real ELF parsing and section-analysis CLI checks for virtual text pointers."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


def image(text_address, immediate):
    raw = bytearray(768)
    raw[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH', raw, 16, 3, 247, 1, text_address,
                     0, 512, 0, 64, 0, 0, 64, 4, 3)
    code = (struct.pack('<BBhI', 0x18, 1, 0, immediate & 0xffffffff)
            + struct.pack('<BBhI', 0, 0, 0, immediate >> 32)
            + b'\x95' + bytes(7))
    raw[128:128 + len(code)] = code
    struct.pack_into('<QQ', raw, 256, text_address, 128)
    names = b'\0.text\0.data.rel.ro\0.shstrtab\0'
    raw[448:448 + len(names)] = names
    headers = [(0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
               (1, 1, 6, text_address, 128, len(code), 0, 0, 8, 0),
               (7, 1, 3, 0x2000, 256, 16, 0, 0, 8, 0),
               (20, 3, 0, 0, 448, len(names), 0, 0, 1, 0)]
    for index, header in enumerate(headers):
        struct.pack_into('<IIQQQQIIQQ', raw, 512 + index * 64, *header)
    return bytes(raw)


class TextPointerAddresses(unittest.TestCase):
    def analyze(self, address, immediate):
        with tempfile.TemporaryDirectory(prefix='text-address-') as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            for name in ('deep_section_analysis.py', 'deep_disassembly.py',
                         'window_elf_reader.py', 'analyze.py'):
                shutil.copyfile(HERE / name, root / 'scripts' / name)
            binary = root / 'evidence/original/fixture/deployed.so'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(image(address, immediate))
            output = root / 'packet'
            result = subprocess.run([sys.executable, '-B', str(root / 'scripts/deep_section_analysis.py'),
                                     '--program', 'fixture', '--output', str(output)],
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            verified = subprocess.run([sys.executable, '-I', '-B', str(output / 'verify.py')],
                                      capture_output=True, text=True, timeout=10)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            return (json.loads((output / 'layer1-data-layout.json').read_bytes()),
                    json.loads((output / 'layer3-cross-section.json').read_bytes()))

    def test_real_virtual_text_pointer_is_counted(self):
        layout, cross = self.analyze(0x1000, 0x1000)
        window = cross['window_data_refs'][0]
        self.assertEqual((window['text_refs'], window['other_refs']), (1, 0))
        pointers = layout['.data.rel.ro']['pointer_like_values']
        self.assertEqual([row['points_to'] for row in pointers], ['0x1000'])

    def test_text_file_offset_is_not_a_virtual_pointer(self):
        _, cross = self.analyze(0x1000, 128)
        window = cross['window_data_refs'][0]
        self.assertEqual((window['text_refs'], window['other_refs']), (0, 1))

    def test_data_layout_reports_the_actual_text_pointer(self):
        layout, _ = self.analyze(0x1000, 0x1000)
        pointers = layout['.data.rel.ro']['pointer_like_values']
        self.assertEqual([(row['offset'], row['points_to']) for row in pointers],
                         [(0, '0x1000')])

    def test_identity_mapped_text_keeps_its_pointers(self):
        layout, cross = self.analyze(128, 128)
        self.assertEqual(cross['window_data_refs'][0]['text_refs'], 1)
        self.assertEqual(layout['.data.rel.ro']['pointer_count'], 2)


if __name__ == '__main__':
    unittest.main()
