#!/usr/bin/env python3
"""Regression receipts must substantiate their claimed case counts.

verify_pump_set_mayhem_params_synthetic.py bound each regression receipt to
its summary row by file hash and length, then trusted the receipt's own
header: it compared the claimed ``case_count`` with the row and required
``mismatches`` to claim empty, but never opened the receipt's case list. A
receipt claiming 7957 cases and zero mismatches while shipping a 3-entry
list passed as a full regression run. The holder-distribution and nested-create
receipts attach their case lists; their header must match the list length.
Historical aggregate and integer-count shapes retain their previous checks.
"""

import ast
import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parent
VERIFIER = SCRIPTS / "verify_pump_set_mayhem_params_synthetic.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_verifier():
    spec = importlib.util.spec_from_file_location("mayhem_synthetic_verifier", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recount = load_verifier().assert_regression_receipt


class RegressionRecountTests(unittest.TestCase):
    def test_shipped_list_is_recounted(self):
        receipt = {"case_count": 7957, "mismatches": [], "cases": [{}, {}, {}]}
        with self.assertRaises(AssertionError):
            recount(receipt, 7957)

    def test_header_must_agree_with_its_own_list(self):
        receipt = {"case_count": 999, "mismatches": [], "cases": [{}, {}, {}]}
        with self.assertRaises(AssertionError):
            recount(receipt, 3)

    def test_a_case_list_without_a_declared_header_is_rejected(self):
        # The agreement check must not be satisfied by the list it checks.
        with self.assertRaises(AssertionError):
            recount({"mismatches": [], "cases": [{}, {}, {}]}, 3)

    def test_consistent_receipt_passes(self):
        for mismatches in ([], 0):
            receipt = {"case_count": 3, "mismatches": mismatches, "cases": [{}, {}, {}]}
            recount(receipt, 3)

    def test_boolean_and_float_headers_are_not_case_counts(self):
        for count in (True, 1.0, "1"):
            with self.subTest(count=count):
                with self.assertRaises(AssertionError):
                    recount({"case_count": count, "cases": [{}], "mismatches": []}, 1)
                with self.assertRaises(AssertionError):
                    recount({"case_count": count, "mismatches": []}, 1)

    def test_expected_count_is_a_nonnegative_integer(self):
        for count in (True, 1.0, -1):
            with self.subTest(count=count):
                with self.assertRaises(AssertionError):
                    recount({"case_count": count, "mismatches": []}, count)

    def test_claimed_mismatches_still_rejected(self):
        receipt = {"case_count": 2, "mismatches": ["case-1"], "cases": [{}, {}]}
        with self.assertRaises(AssertionError):
            recount(receipt, 2)

    def test_header_only_and_count_shapes_preserved(self):
        recount({"case_count": 48, "mismatches": 0}, 48)
        recount({"cases": 48, "mismatches": []}, 48)
        with self.assertRaises(AssertionError):
            recount({"case_count": 47, "mismatches": 0}, 48)

    def test_main_calls_the_recount(self):
        tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node for node in ast.walk(main)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)
                 and node.func.id == "assert_regression_receipt"]
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
