"""Source path attribution must not read beyond its containing section."""
import unittest

from coords import read_cstr_at


class CoordinateBoundsTests(unittest.TestCase):
    def setUp(self):
        self.blob = b'pad!' + b'foo.' + b'rs'
        self.sections = {'.rodata': {'addr': 0x1000, 'offset': 4, 'size': 4}}

    def test_adjacent_bytes_cannot_complete_source_path(self):
        self.assertIsNone(read_cstr_at(self.blob, self.sections, 0x1000, 6))

    def test_exact_section_end_is_valid(self):
        self.assertEqual(read_cstr_at(self.blob, self.sections, 0x1000, 4), b'foo.')
        self.assertEqual(read_cstr_at(self.blob, self.sections, 0x1002, 2), b'o.')

    def test_truncated_file_is_not_a_short_success(self):
        self.assertIsNone(read_cstr_at(self.blob[:6], self.sections, 0x1000, 4))

    def test_invalid_range_is_not_a_string(self):
        self.assertIsNone(read_cstr_at(self.blob, self.sections, 0x1000, -1))
        self.assertIsNone(read_cstr_at(self.blob, self.sections, 0x1004, 1))
        self.assertIsNone(read_cstr_at(self.blob, self.sections, 0x999, 1))


if __name__ == '__main__':
    unittest.main()
