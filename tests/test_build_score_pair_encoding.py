#!/usr/bin/env python3
"""The paired build/score receipt is written as UTF-8 LF.

build_score_pair.py wrote receipt.json and <name>-score.json with bare
write_text, so the locale codec and newline=None translated the trailing
newline per host: the same paired build produced different receipt bytes on
Windows than on the Linux CI, although the receipt is evidence about the pair.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / 'reconstruction/harness/build_score_pair.py'


class BuildScorePairEncodingTests(unittest.TestCase):
    def test_text_writes_pin_utf8_and_lf(self):
        tree = ast.parse(WRITER.read_text(encoding='utf-8'))
        checked = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', '')
            if name not in ('write_text', 'open'):
                continue
            if name == 'open':
                mode = node.args[1].value if len(node.args) > 1 and isinstance(
                    node.args[1], ast.Constant) else None
                if mode not in ('w', 'wt'):
                    continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            where = f'{WRITER.name}:{node.lineno}'
            self.assertIn('encoding', keywords, where)
            self.assertEqual(keywords['encoding'].value, 'utf-8', where)
            self.assertIn('newline', keywords, where)
            self.assertEqual(keywords['newline'].value, '\n', where)
            checked += 1
        # Both the paired receipt and each side's score report are covered.
        self.assertGreaterEqual(checked, 2, 'paired build writers disappeared')


if __name__ == '__main__':
    unittest.main()
