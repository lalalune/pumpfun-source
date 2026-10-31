#!/usr/bin/env python3
"""Mayhem differential and validator reports are written as UTF-8 LF.

The family's report writers used bare write_text: the locale codec and
newline=None translated the trailing newline per host, so the same run
produced different receipt bytes on Windows than on the Linux CI (#1731
class; the AMM family was pinned the same way).
"""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


def takes_output(tree):
    """True when the script publishes a receipt at an --output argument."""
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument" and node.args
        and getattr(node.args[0], "value", None) == "--output"
        for node in ast.walk(tree)
    )


def pinned_writes(tree):
    """Return the receipt writes that pin their encoding and newline."""
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"]


def publishes_through_pump_report(tree, source, seen=()):
    """True when the receipt bytes go through the shared PumpReport publisher.

    Those bytes are composed by the caller and written with ``write``; the
    pinned ``write_text`` shape below no longer appears. The import plus a
    ``write`` call is what identifies the family after that conversion.
    """
    imported = any(
        isinstance(node, ast.ImportFrom) and node.module == "pump_differential_output"
        and any(alias.name == "PumpReport" for alias in node.names)
        for node in ast.walk(tree)
    )
    # Validator subclasses inherit the publisher through their fixture modules.
    # Follow only the local Mayhem family imports, with a cycle guard.
    if not imported:
        for node in ast.walk(tree):
            if (not isinstance(node, ast.ImportFrom) or not node.module
                    or not node.module.startswith("mayhem_") or node.module in seen
                    or not any(alias.name in ("*", "PumpReport") for alias in node.names)):
                continue
            path = SCRIPTS / (node.module + ".py")
            if path.is_file():
                parent = path.read_text(encoding="utf-8")
                # The imported module must itself publish through PumpReport;
                # an unrelated local star import cannot satisfy the guard.
                if publishes_through_pump_report(ast.parse(parent), parent, (*seen, node.module)):
                    imported = True
                    break
    writes = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                 and node.func.attr == "write" for node in ast.walk(tree))
    return imported and writes and "PumpReport(" in source


class MayhemReportEncodingTests(unittest.TestCase):
    def test_every_report_writer_pins_utf8_and_lf(self):
        writers = sorted(p for p in SCRIPTS.glob("mayhem_*.py") if not p.name.startswith("test_"))
        self.assertGreater(len(writers), 10)
        checked = 0
        with_output = 0
        for path in writers:
            with self.subTest(driver=path.name):
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
                pinned = pinned_writes(tree)
                for node in pinned:
                    keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                    self.assertIn("encoding", keywords, f"{path.name}:{node.lineno}")
                    self.assertEqual(keywords["encoding"].value, "utf-8")
                    self.assertIn("newline", keywords)
                    self.assertEqual(keywords["newline"].value, "\n")
                # Byte publishers retain payload bytes; verify any explicit codec.
                for node in ast.walk(tree):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "write" and node.args
                            and isinstance(node.args[0], ast.Call)
                            and isinstance(node.args[0].func, ast.Attribute)
                            and node.args[0].func.attr == "encode"):
                        encode = node.args[0]
                        codec = encode.args or [k.value for k in encode.keywords if k.arg == "encoding"]
                        if codec:
                            self.assertEqual(codec[0].value, "utf-8", f"{path.name}:{node.lineno}")
                checked += len(pinned)
                if takes_output(tree):
                    with_output += 1
                    if not pinned:
                        self.assertTrue(publishes_through_pump_report(tree, source), path.name)
        self.assertGreater(checked, 0)
        self.assertGreater(with_output, 10)


if __name__ == "__main__":
    unittest.main()
