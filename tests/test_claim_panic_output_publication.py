#!/usr/bin/env python3
"""The claim-panic diagnostic must not publish through a link or replace a receipt."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_claim_panic_differential.py'
CANDIDATE = ROOT / 'evidence/original/pump/deployed.so'


class ClaimPanicOutputPublicationTests(unittest.TestCase):
    def invoke(self, output):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(CANDIDATE),
             '--output', str(output)],
            capture_output=True, text=True, timeout=120)

    def test_dangling_symlink_target_is_not_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            escaped = root / 'escaped-report.gz'
            output = root / 'out.gz'
            try:
                output.symlink_to(escaped)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlinks are unavailable: {error}')
            result = self.invoke(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Retain prior diagnostic receipts', result.stderr)
            self.assertFalse(escaped.exists())
            self.assertTrue(output.is_symlink())

    def test_existing_receipt_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.gz'
            output.write_bytes(b'prior receipt\n')
            result = self.invoke(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Retain prior diagnostic receipts', result.stderr)
            self.assertEqual(output.read_bytes(), b'prior receipt\n')

    def test_fresh_output_receives_the_complete_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.gz'
            result = self.invoke(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes()[:2], b'\x1f\x8b')
            self.assertIn('"cases": 2', result.stdout)


if __name__ == '__main__':
    unittest.main()
