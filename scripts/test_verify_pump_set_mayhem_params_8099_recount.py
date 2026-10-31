#!/usr/bin/env python3
"""The 8099 Mayhem regression receipts must substantiate their headers.

verify_pump_set_mayhem_params_8099.py bound each regression receipt to the
regression summary by file hash, then trusted the receipt's own header: it
required the quote-control header to claim 507 cases and 0 mismatches and
the multi-hop header to claim 56 of 56 passed, but never opened the lists
the generators ship beside those claims (``results`` for quote-control,
``cases`` for multi-hop). A receipt claiming full counts while shipping a
3-entry list with a hidden failure passed as a full regression run. When a
receipt includes its list, its header must match a recount of that list.
Count-only shapes retain their previous claimed-count checks.
"""

import ast
import importlib.util
from pathlib import Path
import sys
import types
import unittest


SCRIPTS = Path(__file__).resolve().parent
VERIFIER = SCRIPTS / "verify_pump_set_mayhem_params_8099.py"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_verifier():
    # The verifier imports solders and the differential modules at module
    # level; stub them so the recount helpers load without those packages.
    for name in ("pump_set_mayhem_params_synthetic_cpi",
                 "verify_pump_set_mayhem_params_synthetic"):
        stub = types.ModuleType(name)
        stub.__file__ = str(SCRIPTS / "stub.py")
        sys.modules.setdefault(name, stub)
    solders = types.ModuleType("solders")
    transaction = types.ModuleType("solders.transaction")
    transaction.VersionedTransaction = object
    solders.transaction = transaction
    sys.modules.setdefault("solders", solders)
    sys.modules.setdefault("solders.transaction", transaction)
    spec = importlib.util.spec_from_file_location("mayhem_8099_verifier", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


verifier = load_verifier()
quote_recount = verifier.assert_quote_regression_recount
curve_recount = verifier.assert_curve_regression_recount


def quote_results(matches):
    return [{"case": f"case-{i}", "matches": ok} for i, ok in enumerate(matches)]


def curve_cases(failing=()):
    return [{"mismatches": ["amount_out"] if i in failing else []}
            for i in range(3)]


class QuoteRegressionRecountTests(unittest.TestCase):
    def test_shipped_list_is_recounted(self):
        receipt = {"cases": 507, "mismatches": 0,
                   "results": quote_results([True, True, True])}
        with self.assertRaises(AssertionError):
            quote_recount(receipt)

    def test_header_must_agree_with_its_own_list(self):
        receipt = {"cases": 999, "mismatches": 0,
                   "results": quote_results([True, True, True])}
        with self.assertRaises(AssertionError):
            quote_recount(receipt)

    def test_hidden_mismatch_rejected(self):
        receipt = {"cases": 3, "mismatches": 0,
                   "results": quote_results([True, False, True])}
        with self.assertRaises(AssertionError):
            quote_recount(receipt)

    def test_consistent_receipt_passes(self):
        quote_recount({"cases": 3, "mismatches": 0,
                       "results": quote_results([True, True, True])})
        quote_recount({"cases": 3, "mismatches": 1,
                       "results": quote_results([True, False, True])})

    def test_count_only_shape_preserved(self):
        quote_recount({"cases": 507, "mismatches": 0})


class CurveRegressionRecountTests(unittest.TestCase):
    def test_shipped_list_is_recounted(self):
        receipt = {"case_count": 56, "passed": 56, "mismatches": [],
                   "cases": curve_cases()}
        with self.assertRaises(AssertionError):
            curve_recount(receipt)

    def test_hidden_failure_rejected(self):
        receipt = {"case_count": 3, "passed": 3, "mismatches": [],
                   "cases": curve_cases(failing=(1,))}
        with self.assertRaises(AssertionError):
            curve_recount(receipt)

    def test_passed_must_match_recount(self):
        receipt = {"case_count": 3, "passed": 3, "mismatches": [1],
                   "cases": curve_cases(failing=(1,))}
        with self.assertRaises(AssertionError):
            curve_recount(receipt)

    def test_consistent_receipt_passes(self):
        curve_recount({"case_count": 3, "passed": 3, "mismatches": [],
                       "cases": curve_cases()})
        curve_recount({"case_count": 3, "passed": 2, "mismatches": [1],
                       "cases": curve_cases(failing=(1,))})

    def test_count_only_shape_preserved(self):
        curve_recount({"case_count": 56, "passed": 56, "mismatches": []})


class RecountWiringTests(unittest.TestCase):
    def test_main_calls_both_recounts(self):
        tree = ast.parse(VERIFIER.read_text(encoding="utf-8"))
        main = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node.func.id for node in ast.walk(main)
                 if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name)]
        self.assertEqual(calls.count("assert_quote_regression_recount"), 1)
        self.assertEqual(calls.count("assert_curve_regression_recount"), 1)


if __name__ == "__main__":
    unittest.main()
