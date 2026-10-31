#!/usr/bin/env python3
"""The donation-relay replay result is written as UTF-8 LF.

replay.py wrote the interim result.json and the extracted crate's
.cargo-checksum.json with write_text and neither an encoding nor a newline, so
the bytes depended on the host locale codec and line separator. The same replay
therefore produced different result bytes and different crate metadata on
Windows than on the Linux CI.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WRITER = ROOT / 'reconstruction/donation-relay/native-linux-v148-20261030/replay.py'


class DonationRelayReplayEncodingTests(unittest.TestCase):
    def test_result_writers_pin_utf8_and_lf(self):
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
        # The interim result and the extracted crate checksum file.
        self.assertEqual(checked, 2, 'replay result writers disappeared')


if __name__ == '__main__':
    unittest.main()
