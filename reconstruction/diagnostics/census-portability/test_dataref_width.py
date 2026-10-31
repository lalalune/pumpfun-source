"""The data-reference audit must not report windows clean after comparing no bytes."""
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
CAPTURE = ROOT / 'evidence/original/pump/deployed.so'


class DatarefWidthTests(unittest.TestCase):
    def audit(self, width):
        return subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('run.py')), 'dataref',
                               '--cand', str(CAPTURE), '--width', width],
                              cwd=ROOT, capture_output=True, text=True, encoding='utf-8')

    def test_non_positive_widths_are_rejected(self):
        for width in ('0', '-8'):
            with self.subTest(width=width):
                result = self.audit(width)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn('--width must be positive', result.stderr)

    def test_default_width_still_runs(self):
        result = self.audit('16')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"width": 16', result.stdout)


if __name__ == '__main__':
    unittest.main()
