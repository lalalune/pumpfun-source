#!/usr/bin/env python3
"""Build, qualification and replay evidence writers pin UTF-8 LF.

The writers used bare write_text: the locale codec and newline=None
translated the trailing newline per host, so the same evidence differed
between Windows and the Linux CI (#1731 class; the differential families
were pinned the same way).
"""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
WRITERS = (
    "pump_build_token_dependency.py",
    "pump_build_verified.py",
    "pump_current673_macos_candidate.py",
    "pump_current673_macos_control.py",
    "pump_macos_frontier_qualification.py",
    "pump_macos_v144_qualification.py",
    "pump_replay_macos_frontier.py",
    "pump_text_layout.py",
    "pump_dependency_cache.py",
)


class BuildEvidenceEncodingTests(unittest.TestCase):
    def test_every_evidence_writer_pins_utf8_and_lf(self):
        checked = 0
        for name in WRITERS:
            with self.subTest(writer=name):
                for node in ast.walk(ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))):
                    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                            and node.func.attr == "write_text"):
                        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
                        self.assertIn("encoding", keywords, f"{name}:{node.lineno}")
                        self.assertEqual(keywords["encoding"].value, "utf-8")
                        self.assertIn("newline", keywords)
                        self.assertEqual(keywords["newline"].value, "\n")
                        checked += 1
        self.assertGreater(checked, 25)


if __name__ == "__main__":
    unittest.main()
