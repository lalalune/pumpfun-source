#!/usr/bin/env python3
"""The link-order receipt is written as UTF-8 LF.

link_order.py records the forwarded linker arguments and every script digest
with write_text and no newline argument, so newline=None let the host translate
the trailing newline: the same link produced a different receipt on Windows
than on the Linux CI, although the receipt is the evidence for that link.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / 'reconstruction/harness/link_order.py'


class LinkOrderReceiptEncodingTests(unittest.TestCase):
    def test_receipt_writer_pins_utf8_and_lf(self):
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
        self.assertEqual(checked, 1, 'the link receipt writer disappeared')


if __name__ == '__main__':
    unittest.main()
