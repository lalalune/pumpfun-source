import importlib.util
from pathlib import Path
import struct, sys, unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject_truncated', ROOT / 'scripts/analyze.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject_truncated'] = subject
spec.loader.exec_module(subject)


def elf(phoff=0, shoff=64, phnum=0):
    b = bytearray(128)
    b[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHIQQQIHHHHHH', b, 16, 3, 247, 1, 0, phoff, shoff, 0, 64, 56, phnum, 64, 1, 0)
    return bytes(b)


class TruncatedElfTables(unittest.TestCase):
    def test_valid_fixture_is_accepted(self):
        self.assertEqual(subject.elf_layout(elf())['elf_extent'], 128)

    def test_truncated_inputs_raise_value_error(self):
        cases = {'header': elf()[:40], 'section table': elf(shoff=4096),
                 'program headers': elf(phoff=4096, phnum=1)}
        for name, data in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                subject.elf_layout(data)


if __name__ == '__main__':
    unittest.main()
