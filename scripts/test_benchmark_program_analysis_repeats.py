"""Check the analysis benchmark rejects a run count with no median."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name('benchmark_program_analysis.py')


class RepeatBoundTests(unittest.TestCase):
    def run_tool(self, repeats):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'evidence/original/pump/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(b'\x7fELF')
            return subprocess.run(
                [sys.executable, '-I', '-B', str(TOOL), '--before', str(root),
                 '--after', str(root), '--repeats', repeats],
                capture_output=True, text=True)

    def test_non_positive_repeats_are_a_usage_error(self):
        for repeats in ('0', '-1'):
            with self.subTest(repeats=repeats):
                completed = self.run_tool(repeats)
                self.assertEqual(completed.returncode, 2, completed.stderr)
                self.assertIn('--repeats must be positive', completed.stderr)
                self.assertNotIn('Traceback', completed.stderr)


if __name__ == '__main__':
    unittest.main()
