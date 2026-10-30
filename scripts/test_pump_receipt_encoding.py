#!/usr/bin/env python3
"""Pump differential receipt writers pin UTF-8 LF (#1731 class)."""
import ast
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
WRITERS = (
    "pump_buyback_recipient_differential.py",
    "pump_quote_control_function_match.py",
    "pump_replay_main_checkpoint.py",
    "pump_set_creator_differential.py",
    "pump_set_mayhem_params_signer_boundary.py",
)


class PumpReceiptEncodingTests(unittest.TestCase):
    def test_every_receipt_writer_pins_utf8_and_lf(self):
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
        self.assertEqual(checked, 5)


if __name__ == "__main__":
    unittest.main()
