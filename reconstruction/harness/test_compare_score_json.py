"""Saved-report admission uses real 1035-window reports, including ambiguity."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compare_scores import load_report


HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / 'pump-main/baseline/score.json'


class ScoreJsonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.rows = json.loads(BASELINE.read_text(encoding='utf-8'))['windows']
        self.key = next(key for key, row in self.rows.items() if row['normalized'])
        self.good = self.rows[self.key]
        self.bad = {**self.good, 'normalized': False, 'raw': False}

    def cli(self, text, *, baseline=False):
        path = self.root / 'input.json'
        path.write_text(text, encoding='utf-8')
        output = self.root / 'comparison.json'
        output.write_text('existing comparison\n', encoding='utf-8')
        inputs = [path, BASELINE] if baseline else [BASELINE, path]
        result = subprocess.run([sys.executable, str(HERE / 'compare_scores.py'),
                                 *map(str, inputs), '--json', str(output)],
                                capture_output=True, text=True, encoding='utf-8')
        return result, output

    def test_duplicate_window_keys_rejected_in_both_orders_and_inputs(self):
        rest = ','.join(json.dumps(k) + ':' + json.dumps(v) for k, v in self.rows.items() if k != self.key)
        for first, last in ((self.bad, self.good), (self.good, self.bad)):
            text = '{"windows":{' + ','.join((json.dumps(self.key) + ':' + json.dumps(first),
                json.dumps(self.key) + ':' + json.dumps(last), rest)) + '}}'
            for baseline in (False, True):
                with self.subTest(first=first['normalized'], baseline=baseline):
                    result, output = self.cli(text, baseline=baseline)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('duplicate JSON key', result.stderr)
                    self.assertEqual(output.read_text(encoding='utf-8'), 'existing comparison\n')

    def test_ambiguous_root_row_and_escaped_keys_rejected(self):
        document = json.dumps({'windows': self.rows})
        window_text = json.dumps(self.rows)
        escaped = ''.join('\\u%04x' % ord(char) for char in self.key)
        invalid = [
            '{"windows":' + window_text + ',"windows":' + window_text + '}',
            document.replace('"normalized": true', '"normalized": false,"normalized": true', 1),
            '{"windows":{' + json.dumps(self.key) + ':' + json.dumps(self.good) + ',"' + escaped + '":' + json.dumps(self.good) + '}}',
        ]
        for text in invalid:
            with self.subTest(text=text[:70]):
                path = self.root / 'ambiguous.json'
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                    load_report(path)

    def test_complete_unique_object_and_inventory_list_remain_valid(self):
        expected = load_report(BASELINE)
        self.assertEqual(len(expected), 1035)
        document = {'windows': [{'start': int(key), 'bytes': row['bytes'],
                                'normalized_matches': row['symbols'] if row['normalized'] else [],
                                'raw_match': row['raw']} for key, row in self.rows.items()]}
        result, output = self.cli(json.dumps(document))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(output.read_text(encoding='utf-8'))['accepted'])
        self.assertEqual(load_report(self.root / 'input.json'), expected)

    def test_unique_real_membership_loss_still_returns_one(self):
        rows = {**self.rows, self.key: self.bad}
        result, output = self.cli(json.dumps({'windows': rows}))
        self.assertEqual(result.returncode, 1, result.stderr)
        comparison = json.loads(output.read_text(encoding='utf-8'))
        self.assertFalse(comparison['accepted'])
        self.assertEqual(comparison['normalized_losses'], [hex(int(self.key))])


if __name__ == '__main__':
    unittest.main()
