#!/usr/bin/env python3
"""Fees differential and validator reports are written as UTF-8 LF.

The family's report writers used bare write_text: the locale codec and
newline=None translated the trailing newline per host, so the same run
produced different receipt bytes on Windows than on the Linux CI (#1731
class; the AMM family was pinned the same way).
"""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


class FeesReportEncodingTests(unittest.TestCase):
    def test_every_report_writer_pins_utf8_and_lf(self):
        writers = sorted(p for p in SCRIPTS.glob("fees_*.py") if not p.name.startswith("test_"))
        self.assertGreater(len(writers), 10)
        checked = 0
        for path in writers:
            with self.subTest(driver=path.name):
                for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "write_text"):
                        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                        self.assertIn("encoding", keywords, f"{path.name}:{node.lineno}")
                        self.assertEqual(keywords["encoding"].value, "utf-8")
                        self.assertIn("newline", keywords)
                        self.assertEqual(keywords["newline"].value, "\n")
                        checked += 1
        self.assertGreater(checked, 10)


if __name__ == "__main__":
    unittest.main()
