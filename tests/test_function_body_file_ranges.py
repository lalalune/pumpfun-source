"""Validate actual captured SBF body reads, including malformed ELF file extents."""
import csv
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_compare_function_bytes as comparison
import pump_quote_control_function_match as matcher


class FunctionBodyRangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'evidence/original/pump/deployed.so'
        cls.image = cls.path.read_bytes()
        cls.sections = matcher.sections(cls.image)
        cls.text = cls.sections['.text']
        with (ROOT / 'reconstruction/base/functions.tsv').open(encoding='utf-8') as stream:
            cls.windows = [(int(row['original_start']), int(row['original_end']))
                           for row in csv.DictReader(stream, delimiter='\t')
                           if row['program'] == 'pump' and row['variant'] == 'selected']

    def test_all_real_inventory_windows_return_their_complete_bytes(self):
        for start, end in self.windows:
            expected_offset = self.text['offset'] + start - self.text['addr']
            raw = comparison.body(self.image, self.sections, start, end - start)
            self.assertEqual(len(raw), end - start)
            self.assertEqual(raw, self.image[expected_offset:expected_offset + end - start])

    def mutant_text_offset(self, value):
        mutant = bytearray(self.image)
        table = struct.unpack_from('<Q', mutant, 0x28)[0]
        width, count, names_index = struct.unpack_from('<HHH', mutant, 0x3a)
        headers = [struct.unpack_from('<IIQQQQIIQQ', mutant, table + i * width)
                   for i in range(count)]
        names_header = headers[names_index]
        names = mutant[names_header[4]:names_header[4] + names_header[5]]
        index = next(i for i, header in enumerate(headers)
                     if names[header[0]:].split(b'\0', 1)[0] == b'.text')
        struct.pack_into('<Q', mutant, table + index * width + 24, value)
        return mutant

    def test_section_metadata_crossing_eof_is_rejected(self):
        start, end = self.windows[0]
        mutant = self.mutant_text_offset(len(self.image) - 8)
        # Section headers stay present and parse successfully; only the declared
        # code file range is malformed. Python slicing used to return eight bytes.
        sections = matcher.sections(mutant)
        self.assertEqual(sections['.text']['size'], self.text['size'])
        with self.assertRaises(ValueError):
            comparison.body(mutant, sections, start, end - start)

    def test_section_file_offset_beyond_eof_is_rejected(self):
        mutant = self.mutant_text_offset(len(self.image) + 8)
        start, end = self.windows[0]
        with self.assertRaises(ValueError):
            comparison.body(mutant, matcher.sections(mutant), start, end - start)

    def test_virtual_out_of_section_ranges_remain_rejected_under_optimization(self):
        start, size = self.text['addr'], self.text['size']
        for address, length in ((start - 8, 8), (start + size, 8),
                                (start, size + 8), (start, 0), (start, -8)):
            with self.subTest(address=address, length=length), self.assertRaises((ValueError, AssertionError)):
                comparison.body(self.image, self.sections, address, length)

    def test_partial_instruction_slots_are_rejected(self):
        start = self.text['addr']
        for address, length in ((start + 1, 8), (start, 1), (start, 9)):
            with self.subTest(address=address, length=length), self.assertRaises(ValueError):
                comparison.body(self.image, self.sections, address, length)

    def test_shared_matcher_reader_returns_the_same_captured_window(self):
        start, end = self.windows[0]
        self.assertEqual(matcher.function_body(self.image, self.sections, start, end - start),
                         comparison.body(self.image, self.sections, start, end - start))

    def test_original_capture_is_unchanged(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),
                         '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d')


if __name__ == '__main__':
    unittest.main()
