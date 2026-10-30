import importlib.util
from pathlib import Path
import sys, unittest, json
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', ROOT / 'scripts/analyze.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)
import struct

def elf(phsize, phnum=0):
    data = bytearray(128)
    data[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH', data, 16, 3, 247, 1, 0, 0, 64, 0, 64, phsize, phnum, 64, 1, 0)
    return data

class Tests(unittest.TestCase):

    def test_no_program_header_table_does_not_require_an_entry_width(self):
        self.assertEqual(subject.elf_layout(elf(0))['elf_extent'], 128)
        self.assertEqual(subject.elf_layout(elf(56))['elf_extent'], 128)
        with self.assertRaises(ValueError):
            subject.elf_layout(elf(0, 1))
