"""Literal text search regressions; never opens or locks the live ledger."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest


HERE = Path(__file__).resolve().parent


def load_matches():
    # The CLI imports POSIX fcntl at module scope. Execute its exact, unmodified
    # pure predicate on Windows too, without stubbing locks or executing main.
    source = HERE / 'log_attempt.py'
    tree = ast.parse(source.read_text(encoding='utf-8'), filename=str(source))
    definitions = [node for node in tree.body
                   if isinstance(node, ast.FunctionDef) and node.name == 'matches']
    if len(definitions) != 1:
        raise AssertionError('Expected one production matches predicate')
    namespace = {'json': json}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace['matches']


matches = load_matches()


def query(text, **filters):
    return SimpleNamespace(text=text, **filters)


class LedgerTextTests(unittest.TestCase):
    def test_retained_attempt_and_metadata_queries_remain_supported(self):
        rows = [json.loads(line) for line in
                (HERE / 'ATTEMPTS.jsonl').read_text(encoding='utf-8').splitlines()
                if line.strip()]
        row = next(row for row in rows if row['attempt_id'] == 'df81e692693f40e38922722b7f3b6437')
        term = '"scoped-bind-map"'
        self.assertIn(term, row['hypothesis'])
        self.assertTrue(matches(row, query(term)))
        self.assertFalse(matches(row, query('"untried-mechanism"')))

    def test_quoted_source_spelling_survives_ledger_serialization(self):
        row = json.loads(json.dumps({'hypothesis': 'pass "sell" into trade_event'}))
        self.assertTrue(matches(row, query('"sell" trade_event')))
        self.assertFalse(matches(row, query('"buy"')))

    def test_unicode_is_case_insensitive_in_nested_evidence(self):
        row = {'hypothesis': 'Compare Δ allocation', 'data': {'notes': '결과 café'}}
        self.assertTrue(matches(row, query('δ CAFÉ 결과')))
        self.assertFalse(matches(row, query('δ missing')))

    def test_literal_backslashes_and_quotes(self):
        row = {'data': {'notes': r'path C:\work\trial; call("sell")'}}
        self.assertTrue(matches(row, query(r'C:\work\trial call("sell")')))
        self.assertFalse(matches(row, query(r'C:\work\absent')))

    def test_existing_word_and_structured_filters(self):
        row = {'target': '0x144508', 'lane': 'sellv2', 'status': 'partial',
               'data': {'notes': 'Fee tuple, no losses'}}
        self.assertTrue(matches(row, query('FEE losses', target='0x144508', lane='sellv2', status='partial')))
        self.assertFalse(matches(row, query('fee missing')))
        for filters in ({'target': '0x80df8'}, {'lane': 'other'}, {'status': 'rejected'}):
            with self.subTest(filters=filters):
                self.assertFalse(matches(row, query('fee', **filters)))
        self.assertTrue(matches(row, query('')))

    def test_serialized_metadata_queries_remain_supported(self):
        self.assertTrue(matches({'lane': 'sellv2'}, query('"lane":')))

    @unittest.skipIf(os.name == 'nt', 'The ledger CLI requires POSIX fcntl')
    def test_cli_searches_persisted_literal_text(self):
        rows = [
            {'lane': 'sellv3', 'target': '0x14a8a8', 'status': 'analyzed',
             'hypothesis': 'pass "sell" into trade_event',
             'data': {'notes': 'Compare Δ layout; 결과 café'}},
            {'lane': 'buyv3', 'target': '0x147ba0', 'status': 'analyzed',
             'hypothesis': 'pass "buy" into trade_event'},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'ATTEMPTS.jsonl'
            ledger.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            env = dict(os.environ, PUMP_SWARM_LEDGER=str(ledger), PYTHONUTF8='1')
            for text in ('"sell"', 'δ 결과 CAFÉ'):
                with self.subTest(text=text):
                    result = subprocess.run(
                        [sys.executable, '-B', str(HERE / 'log_attempt.py'),
                         'search', '--text', text],
                        env=env, capture_output=True, text=True, encoding='utf-8', check=True,
                    )
                    lines = result.stdout.splitlines()
                    self.assertEqual(len(lines), 2)
                    self.assertEqual(json.loads(lines[0])['lane'], 'sellv3')
                    self.assertEqual(lines[1], '# 1 matching rows (1 shown, newest last)')
            self.assertEqual(ledger.read_text(encoding='utf-8'),
                             ''.join(json.dumps(row) + '\n' for row in rows))


if __name__ == '__main__':
    unittest.main()
