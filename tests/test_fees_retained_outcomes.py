"""Contradictory real retained outcomes cannot be masked by producer booleans."""
import ast
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'research/runtime-fees-retained-outcomes-20261101'


def consumer_functions():
    """Load the production validators without starting its eighteen child processes."""
    path = ROOT / 'scripts/fees_validate_all.py'
    tree = ast.parse(path.read_text())
    names = {'CASE_DIFFERENCE_FIELDS', 'OUTCOME_FIELDS', 'EVENT_LOG_SUITES'}
    nodes = [node for node in tree.body
             if (isinstance(node, ast.Assign) and any(
                 isinstance(target, ast.Name) and target.id in names for target in node.targets))
             or isinstance(node, ast.FunctionDef) and node.name in (
                 'exact_json_equal', 'validate_outcomes', 'validate_suite_receipt')]
    namespace = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'),
         namespace)
    return namespace


class FeesRetainedOutcomeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = PACKET / 'bounded-receipts.json.gz'
        cls.suites = json.loads(gzip.decompress(cls.corpus.read_bytes()))['suites']
        cls.consumer = consumer_functions()

    def test_real_retained_receipts_through_the_aggregate_cli(self):
        spec = importlib.util.spec_from_file_location('fees_receipt_replay', PACKET / 'replay.py')
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        control = replay.replay(ROOT, self.corpus, 'control')
        self.assertEqual(control['exit_code'], 0, control)
        self.assertEqual(control['published_cases'], 36)
        self.assertEqual(control['published_mismatches'], [])
        corrupted = replay.replay(ROOT, self.corpus, 'contradiction')
        self.assertNotEqual(corrupted['exit_code'], 0, corrupted)
        self.assertIn('retained error differs', corrupted['stderr'])
        self.assertTrue(corrupted['prior_output_preserved'])
        self.assertFalse(corrupted['published_contradiction'])

    def test_every_declared_semantic_field_is_checked(self):
        validate = self.consumer['validate_suite_receipt']
        for name, suite in self.suites.items():
            self.assertEqual(validate(name, copy.deepcopy(suite)), [])
            for field in self.consumer['OUTCOME_FIELDS'][name]:
                with self.subTest(suite=name, field=field):
                    document = copy.deepcopy(suite)
                    document['cases'][0]['candidate'][field] = 'contradictory test value'
                    with self.assertRaises(AssertionError):
                        validate(name, document)
                    del document['cases'][0]['candidate'][field]
                    with self.assertRaises(AssertionError):
                        validate(name, document)

    def test_recursive_json_types_are_not_coerced(self):
        equal = self.consumer['exact_json_equal']
        for left, right in ((False, 0), (True, 1), (0, 0.0), ({'x': [True]}, {'x': [1]})):
            with self.subTest(left=left, right=right):
                self.assertFalse(equal(left, right))
        validate = self.consumer['validate_suite_receipt']
        for name, suite in self.suites.items():
            for field in self.consumer['OUTCOME_FIELDS'][name]:
                document = copy.deepcopy(suite)
                del document['cases'][0]['original'][field]
                del document['cases'][0]['candidate'][field]
                with self.subTest(suite=name, missing_both=field), self.assertRaises(AssertionError):
                    validate(name, document)

    def test_query_and_missing_outcomes_cannot_use_an_empty_difference_flag(self):
        validate = self.consumer['validate_suite_receipt']
        for name, suite in self.suites.items():
            document = copy.deepcopy(suite)
            document['cases'][0].update(match=True, different_fields=[])
            del document['cases'][0]['candidate']
            with self.subTest(suite=name), self.assertRaises(AssertionError):
                validate(name, document)
        for candidate in ({}, {'fees': [0, 0, 0]}, {'error': 'contradictory query result'}):
            document = copy.deepcopy(self.suites['queries'])
            document['cases'][0].update(match=True, different_fields=[], candidate=candidate)
            with self.subTest(candidate=candidate), self.assertRaises(AssertionError):
                validate('queries', document)

    def test_a_suite_without_a_declared_case_count_is_rejected(self):
        # Defaulting the count to len(cases) makes the check true by
        # construction, so a producer that stopped declaring it still passed.
        validate = self.consumer['validate_suite_receipt']
        for name, suite in self.suites.items():
            document = copy.deepcopy(suite)
            del document['case_count']
            with self.subTest(suite=name), self.assertRaisesRegex(AssertionError, 'case_count'):
                validate(name, document)
            document['case_count'] = len(document['cases']) + 1
            with self.subTest(suite=name, inflated=True), self.assertRaisesRegex(AssertionError, 'case_count'):
                validate(name, document)

    def test_aggregate_cli_rejects_undeclared_counts_before_replacing_output(self):
        # These adapters only return retained bytes; none executes a VM suite.
        spec = importlib.util.spec_from_file_location('fees_count_receipt_replay', PACKET / 'replay.py')
        replay = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(replay)
        with tempfile.TemporaryDirectory() as temporary:
            corpus = Path(temporary) / 'missing-count.json.gz'
            document = copy.deepcopy({'suites': self.suites})
            for suite in document['suites'].values():
                del suite['case_count']
            corpus.write_bytes(gzip.compress(json.dumps(document).encode(), mtime=0))
            result = replay.replay(ROOT, corpus, 'control')
            self.assertNotEqual(result['exit_code'], 0, result)
            self.assertIn('case_count must be declared', result['stderr'])
            self.assertTrue(result['prior_output_preserved'])
            self.assertIsNone(result['published_cases'])

    def test_only_event_lines_from_selected_producer_logs_are_compared(self):
        validate = self.consumer['validate_suite_receipt']
        for name in self.consumer['EVENT_LOG_SUITES']:
            document = copy.deepcopy(self.suites[name])
            document['cases'][0]['candidate']['logs'].append('Program log: different diagnostic')
            self.assertEqual(validate(name, document), [])
            document['cases'][0]['candidate']['logs'].append('Program data: Y29udHJhZGljdGlvbg==')
            with self.subTest(suite=name), self.assertRaises(AssertionError):
                validate(name, document)


if __name__ == '__main__':
    unittest.main()
