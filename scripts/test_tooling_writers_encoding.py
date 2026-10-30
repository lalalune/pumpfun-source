#!/usr/bin/env python3
"""Core tooling text writers pin UTF-8 LF (#1731 class; completes the sweep)."""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


class ToolingWritersEncodingTests(unittest.TestCase):
    def test_every_nonfamily_text_writer_pins_utf8_and_lf(self):
        """All scripts outside the already-pinned families (pump_, mayhem_,
        fees_, pump_amm_ prefixes are covered by their own pin tests)."""
        covered = ('pump_', 'mayhem_', 'fees_', 'test_')
        writers = [p for p in sorted(SCRIPTS.glob('*.py'))
                   if not p.name.startswith(covered)]
        checked = 0
        for path in writers:
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == 'write_text'):
                    with self.subTest(writer=path.name, line=node.lineno):
                        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                        self.assertIn("encoding", keywords)
                        self.assertEqual(keywords["encoding"].value, "utf-8")
                        self.assertIn("newline", keywords)
                        self.assertEqual(keywords["newline"].value, "\n")
                    checked += 1
        self.assertGreater(checked, 30)


if __name__ == "__main__":
    unittest.main()
