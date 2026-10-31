#!/usr/bin/env python3
"""Fees differential and validator reports are written as UTF-8 LF.

The family's report writers used bare write_text: the locale codec and
newline=None translated the trailing newline per host, so the same run
produced different receipt bytes on Windows than on the Linux CI (#1731
class; the AMM family was pinned the same way).

Most of the family has since moved to shared publishers that pin their own
bytes: pump_differential_output.PumpReport and probe_report.write_json_report.
Every script that takes --output must use one of those or a pinned write_text.
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


def write_text_calls(tree):
    """Return the write_text receipt calls; each must pin encoding and newline."""
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "write_text"]


def imports(tree, module, name):
    return any(
        isinstance(node, ast.ImportFrom) and node.module == module
        and any(alias.name == name for alias in node.names)
        for node in ast.walk(tree)
    )


def calls(tree, name):
    """True when the tree calls name directly or as an attribute."""
    return any(
        isinstance(node, ast.Call) and (
            (isinstance(node.func, ast.Name) and node.func.id == name)
            or (isinstance(node.func, ast.Attribute) and node.func.attr == name))
        for node in ast.walk(tree)
    )


def publishes_through_pump_report(tree):
    """PumpReport composes nothing itself; the caller passes bytes to write()."""
    return (imports(tree, "pump_differential_output", "PumpReport")
            and calls(tree, "PumpReport") and calls(tree, "write"))


def publishes_through_json_report(tree):
    """write_json_report opens its staging file as UTF-8 with LF newlines."""
    return (imports(tree, "probe_report", "write_json_report")
            and calls(tree, "write_json_report"))


class FeesReportEncodingTests(unittest.TestCase):
    def test_every_report_writer_pins_utf8_and_lf(self):
        writers = sorted(p for p in SCRIPTS.glob("fees_*.py") if not p.name.startswith("test_"))
        self.assertGreater(len(writers), 10)
        with_output = 0
        for path in writers:
            with self.subTest(driver=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                pinned = write_text_calls(tree)
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
                if takes_output(tree):
                    with_output += 1
                    self.assertTrue(
                        pinned or publishes_through_pump_report(tree)
                        or publishes_through_json_report(tree),
                        f"{path.name} takes --output but has no pinned report writer")
        self.assertGreater(with_output, 10)


if __name__ == "__main__":
    unittest.main()
