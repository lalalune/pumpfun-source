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

    def test_captured_images_parse_without_sdk(self):
        root=Path(__file__).resolve().parents[2]
        for path in (root/'evidence/original').glob('*/deployed.so'):
            with self.subTest(program=path.parent.name):
                function_symbols(path.read_bytes())


if __name__ == '__main__': unittest.main()
