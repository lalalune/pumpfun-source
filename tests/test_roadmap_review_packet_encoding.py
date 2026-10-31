#!/usr/bin/env python3
"""The reviewed-regeneration packet is written as UTF-8 LF.

roadmap-reviewed-regeneration/generate.py staged observations.json, inputs.json
and manifest.json with write_text and no newline argument. newline=None let each
host translate the trailing newline, so the packet's own manifest digests (and
therefore the packet compared across hosts) differed between Windows and the
Linux CI.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / 'reconstruction/diagnostics/roadmap-reviewed-regeneration/generate.py'


class RoadmapReviewPacketEncodingTests(unittest.TestCase):
    def test_packet_writers_pin_utf8_and_lf(self):
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
        # observations.json, inputs.json and manifest.json.
        self.assertEqual(checked, 3, 'reviewed-regeneration packet writers disappeared')


if __name__ == '__main__':
    unittest.main()
