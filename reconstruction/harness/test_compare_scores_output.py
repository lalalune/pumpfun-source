"""The comparison CLI must preserve its inputs and prior comparison receipts."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from compare_scores import main


class ComparisonOutputTests(unittest.TestCase):
    def test_existing_output_and_input_aliases_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, candidate, receipt = [root / name for name in ('baseline.json', 'candidate.json', 'receipt.json')]
            document = json.dumps({'windows': {'0': {'bytes': 8, 'normalized': True, 'raw': False}}})
            baseline.write_text(document, encoding='utf-8')
            candidate.write_text(document, encoding='utf-8')
            receipt.write_text('retained receipt\n', encoding='utf-8')
            before = {path: path.read_bytes() for path in (baseline, candidate, receipt)}
            for destination in (baseline, candidate, receipt, root / 'nested' / '..' / 'baseline.json'):
                for path, contents in before.items():
                    path.write_bytes(contents)
                with self.subTest(destination=destination), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        main([str(baseline), str(candidate), '--json', str(destination)])
                    self.assertEqual(error.exception.code, 2)
                    self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_new_nested_output_still_records_comparison(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temporary)
            baseline, candidate = root / 'baseline.json', root / 'candidate.json'
            document = json.dumps({'windows': {'0': {'bytes': 8, 'normalized': True, 'raw': False}}})
            for path in (baseline, candidate):
                path.write_text(document, encoding='utf-8')
            output = root / 'new' / 'receipt.json'
            self.assertEqual(main([str(baseline), str(candidate), '--json', str(output)]), 0)
            self.assertTrue(json.loads(output.read_text(encoding='utf-8'))['accepted'])


if __name__ == '__main__':
    unittest.main()
