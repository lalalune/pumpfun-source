"""One malformed saved ledger row must not cost the whole applicability report."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attempt_applicability import FIELDS

TOOL = Path(__file__).resolve().with_name('attempt_applicability.py')
CONTEXT = {field: 'a' * 64 for field in FIELDS}
PAYLOAD = b'trial verdict'


def attempt(path, digest):
    return {'target': '0x10', 'approach': 'shape-A',
            'data': {'context': CONTEXT, 'evidence': [{'path': path, 'sha256': digest}]}}


class MalformedRowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'evidence').mkdir()
        (self.root / 'evidence/verdict.json').write_bytes(PAYLOAD)
        (self.root / 'context.json').write_text(json.dumps(CONTEXT), encoding='utf-8')
        self.good = json.dumps(attempt('verdict.json', hashlib.sha256(PAYLOAD).hexdigest())).encode()

    def inspect(self, second_row):
        ledger = self.root / 'ledger.jsonl'
        ledger.write_bytes(self.good + b'\n' + second_row + b'\n')
        result = subprocess.run([sys.executable, '-B', str(TOOL),
            '--ledger', str(ledger), '--context', str(self.root / 'context.json'),
            '--evidence-root', str(self.root / 'evidence'), '--target', '16',
            '--approach', 'shape-A'], capture_output=True, text=True)
        self.assertTrue(result.stdout, result.stderr[-300:])
        self.assertNotIn('Traceback', result.stderr)
        return result.returncode, json.loads(result.stdout)

    def assert_row_error(self, second_row):
        code, report = self.inspect(second_row)
        self.assertEqual(code, 2)
        self.assertEqual([row['applicability'] for row in report['rows']], ['compatible'])
        self.assertEqual([error['line'] for error in report['parse_errors']], [2])

    def test_row_that_is_not_utf8_is_reported_with_its_line(self):
        self.assert_row_error(b'{"target":"0x10","approach":"\xff"}')

    def test_row_nested_past_the_parser_limit_is_reported_with_its_line(self):
        self.assert_row_error(b'[' * 200000)

    def test_evidence_paths_the_filesystem_cannot_name_are_unverifiable(self):
        for name in ('verdict\0.json', 'verdict\ud800.json'):
            with self.subTest(name=name):
                code, report = self.inspect(json.dumps(attempt(name, 'b' * 64)).encode())
                self.assertEqual(code, 0)
                self.assertEqual([row['applicability'] for row in report['rows']],
                                 ['compatible', 'unverifiable'])
                self.assertEqual(len(report['rows'][1]['reasons']), 1)
                self.assertIn('unreadable evidence', report['rows'][1]['reasons'][0])


if __name__ == '__main__':
    unittest.main()
