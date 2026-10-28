#!/usr/bin/env python3
"""Mutation tests ensuring the byte comparator cannot hide code/padding changes."""
import subprocess
import sys
import unittest
from pathlib import Path

from compare import compare


class ComparisonTests(unittest.TestCase):
    def test_equal(self): self.assertTrue(compare(b'abc\0\0',b'abc\0\0')['full_byte_equality'])
    def test_code_mutation(self): self.assertEqual(compare(b'abc\0\0',b'axc\0\0')['first_difference'],1)
    def test_padding_mutation(self): self.assertEqual(compare(b'abc\0\0',b'abc\0x')['first_difference'],4)
    def test_truncated_padding(self): self.assertFalse(compare(b'abc\0\0',b'abc\0')['full_byte_equality'])
    def test_extended_padding(self): self.assertFalse(compare(b'abc\0',b'abc\0\0')['full_byte_equality'])
    def test_empty(self): self.assertEqual(compare(b'a',b'')['first_difference'],0)


class Mayhem441SourceTests(unittest.TestCase):
    def test_source_regression_guard(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-B", str(root / "research/mayhem-441-source-regression.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn("Mayhem 441 source regression checks: PASS", result.stdout)


if __name__=='__main__': unittest.main()
