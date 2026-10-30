from pathlib import Path
import struct
from types import SimpleNamespace
import tempfile
import unittest
import analyze as adapter


def image(address=0x1000, offset=0x20, relocation=None, size=16):
    blob = bytearray(0x200)
    value = 0xfedcba9876543210
    struct.pack_into('<BBhI', blob, offset, 0x18, 1, 0, value & 0xffffffff)
    struct.pack_into('<II', blob, offset + 8, 0, value >> 32)
    struct.pack_into('<QQ', blob, 0x180, address if relocation is None else relocation, 8)
    return SimpleNamespace(
        b=bytes(blob), symbols={}, lo=offset, hi=offset + size,
        secs={'.text': (0, 1, 6, address, offset, size, 0, 0, 8, 0),
              '.rel.dyn': (0, 9, 0, 0, 0x180, 16, 0, 0, 8, 16)},
    )


class TextRelocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = adapter.reviewed(corrected=False)
        cls.new = adapter.reviewed()

    def test_text_virtual_addresses_are_translated_to_file_positions(self):
        for address, offset in [(0x1000, 0x20), (0x20, 0x100)]:
            with self.subTest(address=address, offset=offset):
                elf = image(address, offset)
                self.assertEqual(self.old.analyze_relocations(elf)['entries'][0]['target_section'], 'unknown')
                result = self.new.analyze_relocations(elf)
                self.assertEqual(result['entries_in_text'], 1)
                self.assertEqual(result['entries'][0]['target_section'], '.text')
                self.assertEqual(result['entries'][0]['resolved_value'], '0xfedcba9876543210')

    def test_file_offset_alone_does_not_establish_a_text_relocation(self):
        elf = image(relocation=0x20)
        self.assertEqual(self.old.analyze_relocations(elf)['entries'][0]['target_section'], '.text')
        entry = self.new.analyze_relocations(elf)['entries'][0]
        self.assertEqual(entry['target_section'], 'unknown')
        self.assertNotIn('resolved_value', entry)

    def test_resolution_never_reads_past_the_text_section(self):
        elf = image(size=8)
        entry = self.new.analyze_relocations(elf)['entries'][0]
        self.assertEqual(entry['target_section'], '.text')
        self.assertNotIn('resolved_value', entry)
        elf = image(relocation=0x1008)
        self.assertNotIn('resolved_value', self.new.analyze_relocations(elf)['entries'][0])

    def test_all_nine_retained_capture_reports_are_unchanged(self):
        paths = sorted((adapter.ROOT / 'evidence').glob('**/capture.json'))
        self.assertEqual(len(paths), 9)
        for path in paths:
            with self.subTest(capture=str(path)):
                elf = self.new.Elf(path.parent / 'deployed.so')
                self.assertEqual(self.old.analyze_relocations(elf), self.new.analyze_relocations(elf))

    def test_source_drift_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.py'
            path.write_text('raise RuntimeError("must not execute")')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                adapter.reviewed(path)


if __name__ == '__main__':
    unittest.main()
