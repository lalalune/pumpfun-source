import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from compare_scores import compare, load_report, main


def window(normalized=False, raw=False, size=8):
    return {'normalized': normalized, 'raw': raw, 'bytes': size}


class ScoreComparisonTests(unittest.TestCase):
    def test_equal_counts_do_not_hide_membership_loss(self):
        result = compare({0: window(True), 8: window()}, {0: window(), 8: window(True)})
        self.assertFalse(result['accepted'])
        self.assertEqual(result['normalized_losses'], ['0x0'])
        self.assertEqual(result['normalized_gains'], ['0x8'])
        self.assertEqual(result['normalized_lost_bytes'], 8)

    def test_raw_regression_fails_even_with_normalized_gain(self):
        result = compare({0: window(True, True), 8: window()}, {0: window(True), 8: window(True)})
        self.assertFalse(result['accepted'])
        self.assertEqual(result['raw_losses'], ['0x0'])

    def test_inventory_changes_fail_closed(self):
        for after, key in [({}, 'missing'), ({0: window(size=16)}, 'resized'), ({0: window(), 8: window()}, 'added')]:
            with self.subTest(key=key):
                result = compare({0: window()}, after)
                self.assertFalse(result['accepted'])
                self.assertTrue(result[key])

    def test_preservation_and_gains_pass(self):
        self.assertTrue(compare({0: window()}, {0: window(True, True)})['accepted'])
        self.assertTrue(compare({0: window(True)}, {0: window(True)})['accepted'])

    def test_supported_formats_and_invalid_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'score.json'
            path.write_text(json.dumps({'windows': [{'start': 8, 'bytes': 16, 'normalized_matches': ['symbol'], 'raw_match': False}]}))
            self.assertEqual(load_report(path), {8: window(True, size=16)})
            invalid = [[], {}, {'8': window(False, True)}, {'8': window(size=7)}, {'8': window(), '0x8': window()}, {'-8': window()}]
            for rows in invalid:
                with self.subTest(rows=rows):
                    path.write_text(json.dumps({'windows': rows}))
                    with self.assertRaises(ValueError): load_report(path)

    def test_cli_status_and_saved_report(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            before, after, output = [Path(temp) / name for name in ('before.json', 'after.json', 'nested/report.json')]
            before.write_text(json.dumps({'windows': {'0': window(True, True)}}))
            after.write_text(json.dumps({'windows': {'0': window(True)}}))
            self.assertEqual(main([str(before), str(after), '--json', str(output)]), 1)
            self.assertEqual(json.loads(output.read_text())['raw_losses'], ['0x0'])


if __name__ == '__main__': unittest.main()
