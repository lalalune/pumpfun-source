"""Analysis reports must not replace the captured original or window inventory.

The tools run from an isolated copy, so a regression cannot damage this checkout.
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parents[1]
ORIGINAL = REPO / 'evidence/original/pump/deployed.so'
POINTER = b'../../evidence/original/pump/deployed.so'


class ReportScorerInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.tools = self.root / 'reconstruction/harness'
        self.tools.mkdir(parents=True)
        for script in HARNESS.glob('*.py'):
            if not script.name.startswith('test_'):
                shutil.copy(script, self.tools)
        base = self.root / 'reconstruction/base'
        base.mkdir()
        self.inventory = base / 'functions.tsv'
        shutil.copy(REPO / 'reconstruction/base/functions.tsv', self.inventory)
        # A core.symlinks=false checkout stores the link as this regular file.
        (base / 'original.so').write_bytes(POINTER)
        self.captured = self.root / 'evidence/original/pump/deployed.so'
        self.captured.parent.mkdir(parents=True)
        shutil.copy(ORIGINAL, self.captured)
        self.candidate = self.root / 'candidate.so'
        shutil.copy(ORIGINAL, self.candidate)

    def assert_rejected(self, tool, destination):
        before = destination.read_bytes()
        result = subprocess.run(
            [sys.executable, '-B', str(self.tools / tool[0]), *tool[1:],
             '--cand', str(self.candidate), '--json', str(destination)],
            cwd=self.root, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('report destination aliases an input', result.stderr)
        self.assertEqual(destination.read_bytes(), before)

    def test_coordinate_report_cannot_replace_the_inventory(self):
        self.assert_rejected(['coords.py', 'unmatched'], self.inventory)

    def test_coordinate_report_cannot_replace_the_captured_original(self):
        self.assert_rejected(['coords.py', 'unmatched'], self.captured)

    def test_triage_report_cannot_replace_the_captured_original(self):
        self.assert_rejected(['triage.py'], self.captured)


if __name__ == '__main__':
    unittest.main()
