"""Receipt publication must not replace an input admitted by any matrix row."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiment_runner import run_trial

H = Path(__file__).resolve().parent
SEED = b'{"attempt":"attempt-seed","marker":"preserve-me"}\n'


def predicate(input_path, launched):
    return [sys.executable, '-c',
            'import json,sys; from pathlib import Path; '
            'value=json.loads(Path(sys.argv[1]).read_text())["marker"]; '
            'Path(sys.argv[2]).write_text("launched"); '
            'sys.exit(0 if value=="preserve-me" else 1)',
            str(input_path), str(launched)]


class ReceiptInputTests(unittest.TestCase):
    def assert_trial_refused(self, alias):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'; source.mkdir()
            (source / 'lib.rs').write_bytes(b'fn main() {}\n')
            destination = root / 'destination'; destination.mkdir()
            receipt = destination / 'latest.json'; receipt.write_bytes(SEED)
            input_path = receipt
            if alias == 'case':
                input_path = destination / 'LATEST.JSON'
                if not input_path.exists() or not input_path.samefile(receipt):
                    self.skipTest('requires a case-insensitive filesystem')
            elif alias:
                input_path = root / 'input-alias.json'
                try:
                    input_path.symlink_to(receipt)
                except OSError as error:
                    if sys.platform == 'win32' and error.winerror == 1314:
                        self.skipTest('Windows symlink privilege unavailable')
                    raise
            launched = root / 'launched'
            caught = None
            try:
                run_trial(source, predicate(input_path, launched), destination, inputs=[input_path])
            except ValueError as error:
                caught = error
            self.assertEqual(receipt.read_bytes(), SEED, 'declared input overwritten by receipt')
            self.assertFalse(launched.exists(), 'rejected trial must not execute the predicate')
            self.assertIsNotNone(caught)
            self.assertIn('receipt overlaps a declared input', str(caught))
            self.assertEqual(sorted(p.name for p in destination.iterdir()), ['latest.json'])

    def test_receipt_input_is_rejected_before_trial(self):
        self.assert_trial_refused(False)

    def test_receipt_input_alias_is_rejected_before_trial(self):
        self.assert_trial_refused(True)

    def test_receipt_input_case_alias_is_rejected_before_trial(self):
        self.assert_trial_refused('case')

    def test_matrix_protects_later_input_before_earlier_trial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'; source.mkdir()
            (source / 'lib.rs').write_bytes(b'fn main() {}\n')
            out = root / 'out'; (out / 'first').mkdir(parents=True)
            receipt = out / 'first/latest.json'; receipt.write_bytes(SEED)
            first_marker, second_marker = root / 'first-ran', root / 'second-ran'
            rows = [
                {'name': 'first', 'source': str(source), 'command': [sys.executable, '-c',
                 'from pathlib import Path; import sys; Path(sys.argv[1]).write_text("launched")',
                 str(first_marker)]},
                {'name': 'second', 'source': str(source),
                 'command': predicate(receipt, second_marker), 'inputs': [str(receipt)]},
            ]
            matrix = root / 'matrix.json'; matrix.write_text(json.dumps(rows), encoding='utf-8')
            result = subprocess.run([sys.executable, '-B', str(H / 'experiment_runner.py'),
                                     str(matrix), '--out', str(out)],
                                    capture_output=True, timeout=30)
            self.assertEqual(receipt.read_bytes(), SEED, 'earlier row overwrote later declared input')
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn(b'receipt overlaps a declared input', result.stderr)
            self.assertFalse(first_marker.exists())
            self.assertFalse(second_marker.exists())
            self.assertFalse((out / 'second').exists())

    def test_separate_input_reuses_and_replaces_valid_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'; source.mkdir()
            (source / 'lib.rs').write_bytes(b'fn main() {}\n')
            input_path = root / 'input.json'; input_path.write_bytes(SEED)
            destination = root / 'destination'
            command = predicate(input_path, root / 'launched')
            first = run_trial(source, command, destination, inputs=[input_path])
            self.assertEqual(first['status'], 'pass')
            second = run_trial(source, command, destination, inputs=[input_path])
            self.assertTrue(second['reused'])
            self.assertEqual(first['attempt'], second['attempt'])
            self.assertEqual(input_path.read_bytes(), SEED)
            input_path.write_text(json.dumps({'marker': 'changed'}), encoding='utf-8')
            third = run_trial(source, command, destination, inputs=[input_path])
            self.assertEqual(third['status'], 'fail')
            self.assertFalse(third['reused'])
            self.assertNotEqual(third['attempt'], first['attempt'])
            self.assertTrue((destination / first['attempt']).is_dir())
            self.assertEqual(json.loads((destination / 'latest.json').read_bytes())['attempt'], third['attempt'])


if __name__ == '__main__':
    unittest.main()
