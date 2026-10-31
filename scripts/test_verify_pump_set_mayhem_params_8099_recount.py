#!/usr/bin/env python3
"""The 8099 Mayhem regression receipts must substantiate their headers.

verify_pump_set_mayhem_params_8099.py bound each regression receipt to the
regression summary by file hash, then trusted the receipt's own header: it
required the quote-control header to claim 507 cases and 0 mismatches and
the multi-hop header to claim 56 of 56 passed, but never opened the lists
the generators ship beside those claims (``results`` for quote-control,
``cases`` for multi-hop). A receipt claiming full counts while shipping a
3-entry list with a hidden failure passed as a full regression run. Each receipt must retain its typed list and match a recount of that list.
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
    # Load just the production recount functions; do not pollute sys.modules
    # with fake solders/producer modules during combined test discovery.
    tree = ast.parse(VERIFIER.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in ('assert_quote_regression_recount', 'assert_curve_regression_recount')]
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])), str(VERIFIER), 'exec'), namespace)
    return types.SimpleNamespace(**namespace)


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

    def test_missing_or_wrong_type_results_are_rejected(self):
        for results in (None, {}, "missing"):
            with self.subTest(results=results), self.assertRaises(AssertionError):
                quote_recount({"cases": 507, "mismatches": 0, "results": results})
        with self.assertRaises(AssertionError):
            quote_recount({"cases": 1, "mismatches": 0, "results": [{"matches": "true"}]})


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

    def test_actual_producer_header_does_not_require_an_invented_mismatch_index(self):
        curve_recount({'case_count': 3, 'passed': 3, 'cases': curve_cases()})
        with self.assertRaises(AssertionError):
            curve_recount({'case_count': 3, 'passed': 3, 'cases': curve_cases(failing=(1,))})

    def test_missing_or_wrong_type_cases_are_rejected(self):
        for cases in (None, {}, "missing"):
            with self.subTest(cases=cases), self.assertRaises(AssertionError):
                curve_recount({"case_count": 56, "passed": 56, "mismatches": [], "cases": cases})


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
