"""The sell symbol lookup must not count closures of the sell function."""
import importlib.util
import struct
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('closure_sell_score', HERE / 'amm_sell/sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)

PREFIX = '_ZN8pump_amm12instructions4swap4sell8cashback'
SELL = {'name': PREFIX + '17h0123456789abcdefE', 'start': 0x4c750, 'size': 9024}
CLOSURE = {'name': PREFIX + '28_$u7b$$u7b$closure$u7d$$u7d$17hfedcba9876543210E',
           'start': 0x4eaa0, 'size': 64}
OTHER = {'name': '_ZN8pump_amm12instructions4swap3buy17h0123456789abcdefE',
         'start': 0x1000, 'size': 8}


def lookup(*funcs):
    return score.find_sell(SimpleNamespace(funcs=list(funcs)))


class SellSymbolTests(unittest.TestCase):
    def test_closure_does_not_hide_the_sell_function(self):
        for funcs in ((SELL, CLOSURE), (CLOSURE, SELL), (OTHER, CLOSURE, SELL)):
            with self.subTest(order=[row['start'] for row in funcs]):
                try:
                    found = lookup(*funcs)
                except SystemExit as error:
                    self.fail(f'lookup refused a build with one sell function: {error}')
                self.assertEqual(found, SELL)

    def test_real_elf_reader_admits_capture_text_with_synthetic_symbol_metadata(self):
        # This is captured instruction data with an invented symbol table, not
        # a retained native build that emitted a closure or an identity claim.
        capture = HERE.parent / 'evidence/original/pump_amm/deployed.so'
        before = capture.read_bytes()
        original = score.elf_reader.Elf(capture)
        image = bytearray(before)
        sections = list(original.raw)
        names_index = struct.unpack_from('<H', image, 62)[0]
        names_row = sections[names_index]
        names = before[names_row[4]:names_row[4] + names_row[5]]
        string_name = len(names)
        symbol_name = string_name + len(b'.strtab\0')
        names += b'.strtab\0.symtab\0'
        names_at = len(image)
        image.extend(names)
        sections[names_index] = (*names_row[:4], names_at, len(names), *names_row[6:])
        strings = b'\0' + SELL['name'].encode() + b'\0' + CLOSURE['name'].encode() + b'\0'
        strings_at = len(image)
        image.extend(strings)
        strings_index = len(sections)
        sections.append((string_name, 3, 0, 0, strings_at, len(strings), 0, 0, 1, 0))
        symbols_at = len(image)
        text_index = sections.index(original.text)
        value = original.text[3] + score.SELL_START - original.lo
        first_width = score.listing(original, score.SELL_START, score.SELL_SIZE)[0]['len']
        image.extend(bytes(24))  # STN_UNDEF
        image.extend(struct.pack('<IBBHQQ', 1, 18, 0, text_index, value, score.SELL_SIZE))
        image.extend(struct.pack('<IBBHQQ', 2 + len(SELL['name']), 18, 0, text_index, value, first_width))
        sections.append((symbol_name, 2, 0, 0, symbols_at, 72, strings_index, 1, 8, 24))
        while len(image) % 8:
            image.append(0)
        table_at = len(image)
        for section in sections:
            image.extend(struct.pack('<IIQQQQIIQQ', *section))
        struct.pack_into('<Q', image, 40, table_at)
        struct.pack_into('<H', image, 60, len(sections))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic-symbols.so'
            path.write_bytes(image)
            parsed = score.elf_reader.Elf(path)
            self.assertEqual(score.find_sell(parsed), SELL)
            self.assertEqual(sum('4sell8cashback' in row['name'] for row in parsed.funcs), 2)
        self.assertEqual(capture.read_bytes(), before)

    def test_sell_function_alone_is_found(self):
        self.assertEqual(lookup(OTHER, SELL), SELL)

    def test_missing_or_repeated_sell_function_is_still_refused(self):
        repeated = {**SELL, 'name': PREFIX + '17hfedcba9876543210E', 'start': 0x50000}
        for funcs in ((OTHER,), (CLOSURE,), (SELL, repeated)):
            with self.subTest(names=[row['name'][-24:] for row in funcs]):
                with self.assertRaises(SystemExit):
                    lookup(*funcs)


if __name__ == '__main__':
    unittest.main()
