"""Non-permuted .rodata bytes must not be credited to .text content."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import elf_meta_diff

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'


class ElfMetaDiffTests(unittest.TestCase):
    def setUp(self):
        self.original = ORIGINAL.read_bytes()
        header, _, self.sections = elf_meta_diff.parse(self.original)
        self.meaningful = self.original[:header['shoff'] + header['shnum'] * header['shentsize']]

    def compare(self, candidate):
        with tempfile.TemporaryDirectory() as temporary:
            original, stripped = Path(temporary) / 'original.so', Path(temporary) / 'candidate.so'
            original.write_bytes(self.original)
            stripped.write_bytes(candidate)
            with patch.object(sys, 'argv', ['elf_meta_diff.py', str(original), str(stripped)]), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                code = elf_meta_diff.main()
        return code, json.loads(output.getvalue())

    def test_identical_candidate_is_equal(self):
        code, report = self.compare(self.meaningful)
        self.assertEqual((code, report['verdict']), (0, 'meaningful ELF identical'))

    def test_changed_rodata_bytes_stay_a_remaining_difference(self):
        candidate = bytearray(self.meaningful)
        candidate[self.sections['.rodata']['offset'] + 16] ^= 0xff
        code, report = self.compare(candidate)
        self.assertFalse(report['rodata_diff_span']['byte_permutation'])
        self.assertEqual(code, 1)
        self.assertIn('.rodata content', [row['what'] for row in report['build_input_differences']])

    def test_permuted_rodata_is_still_explained(self):
        candidate = bytearray(self.meaningful)
        offset = self.sections['.rodata']['offset']
        first = next(i for i in range(offset, offset + 4096) if candidate[i] != candidate[i + 1])
        candidate[first], candidate[first + 1] = candidate[first + 1], candidate[first]
        code, report = self.compare(candidate)
        self.assertEqual(code, 0)
        self.assertIn('.rodata order', [row['what'] for row in report['text_content_differences']])


if __name__ == '__main__':
    unittest.main()
