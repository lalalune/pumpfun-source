#!/usr/bin/env python3
"""Fixture and capture reads pin UTF-8 regardless of the host locale.

The remaining bare text open() calls all read JSON inputs (imported-lab
fixtures, capture manifests, packet manifests). Today those files are pure
ASCII, but the read codec is the host locale: the first non-ASCII byte in any
of them (e.g. the U+2192 already present in evidence/upstream/pump.json, whose
reader had to be pinned the same way) crashes these tools on cp949 hosts.
"""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


class FixtureReadsEncodingTests(unittest.TestCase):
    def test_every_text_open_pins_utf8(self):
        checked = 0
        for path in sorted(SCRIPTS.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == "open"):
                    mode = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else ""
                    if "b" in str(mode):
                        continue
                    with self.subTest(script=path.name, line=node.lineno):
                        keywords = {keyword.arg for keyword in node.keywords}
                        self.assertIn("encoding", keywords)
                    checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
