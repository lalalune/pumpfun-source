#!/usr/bin/env python3
"""Build-harness publication evidence is written as UTF-8 LF.

integrate.py and fastbuild.py wrote their report, staged manifests, build log
and patch diagnostics with write_text and no newline argument, so newline=None
let each host translate the trailing newline: the same build produced different
evidence bytes on Windows than on the Linux CI.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'reconstruction/harness'
WRITERS = ('integrate.py', 'fastbuild.py')


class BuildHarnessEncodingTests(unittest.TestCase):
    def test_every_evidence_writer_pins_utf8_and_lf(self):
        checked = 0
        for name in WRITERS:
            with self.subTest(writer=name):
                source = (HARNESS / name).read_text(encoding='utf-8')
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
        # The integration report, its three patch diagnostics, the staged
        # manifests and the build log.
        self.assertGreaterEqual(checked, 7, 'build-harness evidence writers disappeared')


if __name__ == '__main__':
    unittest.main()
