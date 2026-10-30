import importlib.util
from pathlib import Path
import sys, unittest, json
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', ROOT / 'scripts/analyze.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)
import struct

def elf(offset=0, terminated=True):
    data = bytearray(256)
    data[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH', data, 16, 3, 247, 1, 0, 0, 64, 0, 64, 56, 0, 64, 2, 1)
    struct.pack_into('<IIQQQQIIQQ', data, 128, offset, 3, 0, 0, 192, 4, 0, 0, 1, 0)
    data[192:196] = b'\x00ok\x00' if terminated else b'abcd'
    return data

class Tests(unittest.TestCase):

    def test_invalid_name_offsets_and_missing_terminators(self):
        for data in (elf(9), elf(0, False)):
            with self.assertRaisesRegex(ValueError, 'section-name'):
                subject.elf_layout(data)
        self.assertEqual(subject.elf_layout(elf())['sections'][1]['name'], '')

    def test_absent_optional_name_table(self):
        data = elf()
        struct.pack_into('<H', data, 62, 0)
        self.assertTrue(all((not s['name'] for s in subject.elf_layout(data)['sections'])))
