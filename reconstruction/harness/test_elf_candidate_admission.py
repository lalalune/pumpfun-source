import struct
import unittest
from elf_symbols import function_symbols
from test_elf_symbols import fixture


class CandidateAdmissionTests(unittest.TestCase):
    def test_foreign_machine_and_nonexecutable_text_are_rejected(self):
        for offset, format, value in ((18, '<H', 62), (64 + 2*64 + 4, '<I', 8),
                                      (64 + 2*64 + 8, '<Q', 2)):
            with self.subTest(offset=offset):
                blob = fixture()
                struct.pack_into(format, blob, offset, value)
                with self.assertRaises(ValueError): function_symbols(blob)

    def test_partial_instruction_function_ranges_are_rejected(self):
        for offset, value in ((504 + 8, 0x1001), (504 + 16, 7)):
            with self.subTest(offset=offset):
                blob = fixture()
                struct.pack_into('<Q', blob, offset, value)
                with self.assertRaisesRegex(ValueError, 'aligned'): function_symbols(blob)

    def test_valid_local_global_and_alias_symbols_remain_intact(self):
        for machine in (247, 263):
            blob = fixture()
            struct.pack_into('<H', blob, 18, machine)
            self.assertEqual(function_symbols(blob),
                             [(0x1000, 8, 'local'), (0x1008, 8, 'global'), (0x1000, 8, 'alias')])


if __name__ == '__main__': unittest.main()
