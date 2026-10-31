import struct
import tempfile
import unittest
from pathlib import Path
from elf_symbols import function_symbols
import score


def fixture():
    blob = bytearray(640)
    blob[:7] = b'\x7fELF\x02\x01\x01'
    struct.pack_into('<HHI', blob, 16, 3, 247, 1)
    struct.pack_into('<H', blob, 52, 64)
    struct.pack_into('<Q', blob, 40, 64)
    struct.pack_into('<HHH', blob, 58, 64, 5, 1)
    names = b'\0.shstrtab\0.text\0.strtab\0.symtab\0'
    blob[384:384+len(names)] = names
    strings = b'\0local\0global\0alias\0'
    blob[440:440+len(strings)] = strings
    for index, values in enumerate([
        (0,0,0,0,0,0,0,0,0,0), (1,3,0,0,384,len(names),0,0,1,0),
        (11,1,6,0x1000,424,16,0,0,8,0), (17,3,0,0,440,len(strings),0,0,1,0),
        (25,2,0,0,480,120,3,0,8,24),
    ]): struct.pack_into('<IIQQQQIIQQ', blob, 64+64*index, *values)
    for index, row in enumerate([(1,2,0,2,0x1000,8),(7,18,2,2,0x1008,8),(14,18,0,2,0x1000,8),(1,17,0,2,0x1000,8)]):
        struct.pack_into('<IBBHQQ', blob, 504+24*index, *row)
    return blob


def lddw_fixture():
    blob = fixture()
    blob[424:440] = struct.pack('<BBhi', 0x18, 0, 0, 0) + bytes(8)
    return blob


class ElfSymbolTests(unittest.TestCase):
    def test_local_hidden_and_alias_functions_but_not_objects(self):
        self.assertEqual(function_symbols(fixture()), [(0x1000,8,'local'),(0x1008,8,'global'),(0x1000,8,'alias')])

    def test_scorer_reads_without_external_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'candidate.so'; path.write_bytes(fixture())
            self.assertEqual(score.candidate_functions(path), function_symbols(fixture()))

    def test_stripped_image_has_no_full_symbol_inventory(self):
        blob=fixture(); struct.pack_into('<I',blob,64+4*64+4,11)
        self.assertEqual(function_symbols(blob), [])

    def test_elf_header_version_must_be_one(self):
        self.assertEqual(len(function_symbols(fixture())), 3)
        for version in (0, 2, 0xffffffff):
            with self.subTest(version=version):
                blob = fixture()
                struct.pack_into('<I', blob, 20, version)
                with self.assertRaisesRegex(ValueError, 'ELF header version 1'):
                    function_symbols(blob)

    def test_header_and_tables_are_bounded(self):
        for edit in [lambda b: b.__setitem__(0,0), lambda b: struct.pack_into('<Q',b,40,600),
                     lambda b: struct.pack_into('<Q',b,64+4*64+32,9999),
                     lambda b: struct.pack_into('<Q',b,64+4*64+56,16),
                     lambda b: struct.pack_into('<I',b,64+4*64+40,99)]:
            blob=fixture();edit(blob)
            with self.assertRaises(ValueError): function_symbols(blob)

    def test_bad_symbol_strings_and_ranges_rejected(self):
        for edit in [lambda b: struct.pack_into('<I',b,504,999),
                     lambda b: struct.pack_into('<Q',b,504+8,0xff8),
                     lambda b: struct.pack_into('<Q',b,504+16,24)]:
            blob=fixture(); edit(blob)
            with self.assertRaises(ValueError): function_symbols(blob)

    def test_all_retained_images_parse_without_sdk(self):
        root=Path(__file__).resolve().parents[2]
        paths = list((root / 'evidence').glob('*/*/deployed.so'))
        self.assertEqual(len(paths), 9)
        for path in paths:
            with self.subTest(program=path.parent.name):
                function_symbols(path.read_bytes())

    def test_complete_lddw_symbol_and_alias_are_valid(self):
        blob = lddw_fixture()
        # Ignore the continuation-start record and make both start aliases span
        # the complete two-slot instruction.
        struct.pack_into('<B', blob, 504 + 24 + 4, 17)
        struct.pack_into('<Q', blob, 504 + 16, 16)
        struct.pack_into('<Q', blob, 504 + 2 * 24 + 16, 16)
        self.assertEqual(function_symbols(blob), [(0x1000, 16, 'local'), (0x1000, 16, 'alias')])

    def test_lddw_continuation_start_is_not_a_function(self):
        blob = lddw_fixture()
        struct.pack_into('<Q', blob, 504 + 16, 16)
        struct.pack_into('<Q', blob, 504 + 2 * 24 + 16, 16)
        with self.assertRaisesRegex(ValueError, 'instruction boundary'):
            function_symbols(blob)
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes(blob)
            with self.assertRaisesRegex(ValueError, 'instruction boundary'):
                score.candidate_functions(candidate)

    def test_function_end_cannot_split_lddw(self):
        blob = lddw_fixture()
        # Keep only the first eight-byte symbol; it cuts the LDDW in half.
        struct.pack_into('<B', blob, 504 + 24 + 4, 17)
        struct.pack_into('<B', blob, 504 + 2 * 24 + 4, 17)
        with self.assertRaisesRegex(ValueError, 'instruction boundary'):
            function_symbols(blob)

    def test_truncated_lddw_text_is_rejected(self):
        blob = lddw_fixture()
        struct.pack_into('<Q', blob, 64 + 2 * 64 + 32, 8)
        struct.pack_into('<B', blob, 504 + 24 + 4, 17)
        struct.pack_into('<B', blob, 504 + 2 * 24 + 4, 17)
        with self.assertRaisesRegex(ValueError, 'truncated instruction'):
            function_symbols(blob)

    def test_duplicate_function_records_remain_deduplicated(self):
        blob = fixture()
        blob[504 + 24:504 + 48] = blob[504:528]
        self.assertEqual(function_symbols(blob), [(0x1000, 8, 'local'), (0x1000, 8, 'alias')])

    def test_unsupported_instruction_versions_are_not_interpreted_as_legacy(self):
        for version in (2, 3, 4, 32):
            with self.subTest(version=version):
                blob = fixture()
                struct.pack_into('<I', blob, 48, version)
                with self.assertRaisesRegex(ValueError, 'legacy SBPFv0/v1'):
                    function_symbols(blob)


if __name__ == '__main__': unittest.main()
