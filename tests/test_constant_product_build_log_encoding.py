#!/usr/bin/env python3
"""The constant-product build log is written as UTF-8 LF.

pump_build_constant_product.py writes the compiler's stdout and stderr next to
the object it produces with write_text and the locale's newline translation.
newline=None let each host translate the trailing newline, so the same build
retained a different build.log on Windows than on the Linux CI.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / 'scripts/pump_build_constant_product.py'


class ConstantProductBuildLogEncodingTests(unittest.TestCase):
    def test_build_log_writer_pins_utf8_and_lf(self):
        source = WRITER.read_text(encoding='utf-8')
        checked = 0
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'write_text'):
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            where = f'{WRITER.name}:{node.lineno}'
            self.assertIn('encoding', keywords, where)
            self.assertEqual(keywords['encoding'].value, 'utf-8', where)
            self.assertIn('newline', keywords, where)
            self.assertEqual(keywords['newline'].value, '\n', where)
            checked += 1
        self.assertEqual(checked, 1, 'the build log writer disappeared')


if __name__ == '__main__':
    unittest.main()
