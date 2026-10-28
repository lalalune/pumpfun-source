"""Reject incomplete or rebound regression evidence at the review gate."""
import copy
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('round37_review', HERE / 'verify_round37_12.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class RegressionGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = HERE / 'r37-genuine-12'
        cls.report = review.read(package / 'full.json.gz')
        cls.archive = package / 'loader-receipts.tar.gz'
        cls.candidate = review.sha(package / 'candidate.so')
        cls.original = review.sha(review.ROOT / 'evidence/original/pump/deployed.so')

    def check(self, report):
        review.check_report(report, self.candidate, self.original)

    def test_complete_report(self):
        self.check(self.report)

    def test_wrong_candidate(self):
        report = copy.deepcopy(self.report)
        report['candidate_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            self.check(report)

    def test_missing_suite(self):
        report = copy.deepcopy(self.report)
        del report['suites']['buy_v2']
        with self.assertRaises(AssertionError):
            self.check(report)

    def test_wrong_case_count(self):
        report = copy.deepcopy(self.report)
        report['suites']['buy_v2']['case_count'] -= 1
        with self.assertRaises(AssertionError):
            self.check(report)

    def test_rebound_suite_candidate(self):
        report = copy.deepcopy(self.report)
        report['suites']['buy_v2']['candidate_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            self.check(report)

    def test_reported_mismatch(self):
        report = copy.deepcopy(self.report)
        report['mismatches'] = ['altered observation']
        with self.assertRaises(AssertionError):
            self.check(report)


    def test_rebound_loader_receipt(self):
        report = copy.deepcopy(self.report)
        report['loader_receipts']['buy_v2']['sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            review.check_loaders(report, self.archive, self.candidate, self.original)

    def test_wrong_loader_count(self):
        report = copy.deepcopy(self.report)
        report['loader_receipts']['buy_v2']['load_count'] += 1
        with self.assertRaises(AssertionError):
            review.check_loaders(report, self.archive, self.candidate, self.original)


if __name__ == '__main__':
    unittest.main()
