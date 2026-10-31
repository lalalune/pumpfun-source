"""Explicit Anchor discriminants are offsets from 6000, as implicit variants are."""
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import callseq  # noqa: E402


class ErrorNames(unittest.TestCase):
    def test_explicit_discriminant_keeps_the_anchor_code(self):
        self.assertEqual(callseq.ERRS.get(6109), 'QuoteChainAccountsRequired')
        self.assertEqual(callseq.ERRS.get(6110), 'QuoteMintNotWritable')
        self.assertTrue(all(6000 <= code < 6200 for code in callseq.ERRS))

    def test_captured_migrate_v2_site_is_named(self):
        # Original migrate_v2 window: the require! at line 335 of migrate_v2.rs.
        capture = Path(__file__).resolve().parents[4] / 'evidence/original/pump/deployed.so'
        blob = capture.read_bytes()
        secs = callseq.sections(blob)
        raw = callseq.body_at(blob, secs, 0x49888, 8888)
        labels = [row[4] for row in callseq.calls(raw, 0x49888, {}, {}, blob, secs)]
        site = [label for label in labels if label and re.search(r'\bL335\b', label)]
        self.assertIn('E6110:QuoteMintNotWritable L335', site)


if __name__ == '__main__':
    unittest.main()
