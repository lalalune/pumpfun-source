#!/usr/bin/env python3
"""Mayhem Linux qualification evidence is written as UTF-8 LF.

build_linux.py saved its receipts, the cargo source-replacement config and the
target compile-set table with write_text and no newline argument, and
prepare_inputs.py did the same for the vendored .cargo-checksum.json and the
prepared-inputs receipt. newline=None let each host translate the trailing
newline, so the same qualification produced different evidence bytes on Windows
than on the Linux CI.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT / 'reconstruction/mayhem/native-linux-qualification'
WRITERS = ('build_linux.py', 'prepare_inputs.py')


class MayhemQualificationEncodingTests(unittest.TestCase):
    def test_every_writer_pins_utf8_and_lf(self):
        checked = 0
        for name in WRITERS:
            with self.subTest(writer=name):
                source = (QUALIFICATION / name).read_text(encoding='utf-8')
                for node in ast.walk(ast.parse(source)):
                    if not (isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Attribute)
                            and node.func.attr == 'write_text'):
                        continue
                    keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                    where = f'{name}:{node.lineno}'
                    self.assertIn('encoding', keywords, where)
                    self.assertEqual(keywords['encoding'].value, 'utf-8', where)
                    self.assertIn('newline', keywords, where)
                    self.assertEqual(keywords['newline'].value, '\n', where)
                    checked += 1
        # build_linux: save(), cargo config and compile-set table;
        # prepare_inputs: crate checksum and receipt.
        self.assertGreaterEqual(checked, 5, 'qualification evidence writers disappeared')


if __name__ == '__main__':
    unittest.main()
