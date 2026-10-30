"""Conflicting score baseline switches must not overwrite an input report."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_elf_symbols import fixture

ROOT = Path(__file__).resolve().parents[2]
SCORER = ROOT / 'reconstruction/harness/score.py'
BASELINE = ROOT / 'reconstruction/pump-main/baseline/score.json'

class BaselineOptionTests(unittest.TestCase):
    def test_conflicting_switches_reject_and_preserve_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate, baseline = root / 'candidate.so', root / 'baseline.json'
            candidate.write_bytes(fixture())
            original = BASELINE.read_bytes()
            for order in (['--baseline', str(baseline), '--no-baseline'],
                          ['--no-baseline', '--baseline', str(baseline)]):
                with self.subTest(order=order):
                    baseline.write_bytes(original)
                    result = subprocess.run([sys.executable, str(SCORER), str(candidate), *order,
                                             '--json', str(baseline)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertIn('not allowed with argument', result.stderr)
                    self.assertEqual(baseline.read_bytes(), original)

if __name__ == '__main__':
    unittest.main()
