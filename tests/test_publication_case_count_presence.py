"""A published report must declare case_count, not be let off by a default.

The shared corpus check compared the number of cases with
``report.get('case_count', len(report['cases']))``. When the key is absent the
default is the left-hand value, so the comparison is true by construction and
a writer that stopped declaring case_count would still pass every publication
test that inherits the check.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import publication_cli_support as support


class CaseCountPresenceTests(unittest.TestCase):
    def corpus(self, report):
        """Run the shared corpus check against a fixed report instead of a real CLI."""
        case = unittest.TestCase()
        case.NAMES = ('fake',)
        case.EXPECTED = {'fake': 2}
        case.PROOF_ENV = 'PUMP_PUBLICATION_PROOF_OUT'
        completed = support.subprocess.CompletedProcess(args=[], returncode=0, stdout='', stderr='')
        case.invoke = lambda name, mode='full', output=None, cwd=None: completed
        case.report = lambda: report
        with patch.dict(support.os.environ):
            support.os.environ.pop(case.PROOF_ENV, None)
            support.PublicationCase.test_full_corpora(case)

    def test_a_report_without_case_count_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'case_count'):
            self.corpus({'mismatches': [], 'cases': [{}, {}]})

    def test_a_report_with_the_declared_count_is_accepted(self):
        self.corpus({'mismatches': [], 'case_count': 2, 'cases': [{}, {}]})

    def test_a_report_whose_count_disagrees_with_its_cases_is_rejected(self):
        with self.assertRaises(AssertionError):
            self.corpus({'mismatches': [], 'case_count': 3, 'cases': [{}, {}]})

    def test_non_integer_counts_are_rejected(self):
        for count in (2.0, True, '2'):
            with self.subTest(count=count), self.assertRaises(AssertionError):
                self.corpus({'mismatches': [], 'case_count': count, 'cases': [{}, {}]})

    def test_case_objects_are_not_case_lists(self):
        with self.assertRaises(AssertionError):
            self.corpus({'mismatches': [], 'case_count': 2, 'cases': {'one': {}, 'two': {}}})


if __name__ == '__main__':
    unittest.main()
