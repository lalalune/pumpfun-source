"""Function byte admission must not rely on permissive Python slice semantics."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import score


class BodyBoundsTests(unittest.TestCase):
    def setUp(self):
        self.image = b'header!!' + bytes(range(16)) + b'other section'
        self.sections = {'.text': {'addr': 0x1000, 'offset': 8, 'size': 16}}

    def test_exact_section_and_end_boundaries(self):
        self.assertEqual(score.body(self.image, self.sections, 0x1000, 16), bytes(range(16)))
        self.assertEqual(score.body(self.image, self.sections, 0x1008, 8), bytes(range(8, 16)))
        self.assertEqual(score.body(self.image, self.sections, 0x1010, 0), b'')

    def test_crossing_into_other_section_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside .text'):
            score.body(self.image, self.sections, 0x1008, 16)

    def test_before_and_after_section_are_rejected(self):
        for start, size in ((0xff8, 8), (0x1010, 8), (0x2000, 0)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                score.body(self.image, self.sections, start, size)

    def test_truncated_file_is_rejected_instead_of_short_read(self):
        with self.assertRaisesRegex(ValueError, 'beyond the ELF file'):
            score.body(self.image[:20], self.sections, 0x1008, 8)

    def test_negative_and_noninteger_bounds_are_rejected(self):
        for start, size in ((0x1000, -1), (-1, 8), (0x1000, True), (0x1000, 1.5)):
            with self.subTest(start=start, size=size), self.assertRaises(ValueError):
                score.body(self.image, self.sections, start, size)
        for field in ('addr', 'offset', 'size'):
            sections = {'.text': {**self.sections['.text'], field: -1}}
            with self.subTest(field=field), self.assertRaises(ValueError):
                score.body(self.image, sections, 0x1000, 8)

    def test_score_rejects_invalid_symbol_before_matching(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes(self.image)
            with patch.object(score, 'sections', return_value=self.sections), \
                 patch.object(score, 'candidate_functions', return_value=[(0x1008, 16, 'bad')]), \
                 patch.object(score, 'original_windows') as originals:
                with self.assertRaisesRegex(ValueError, 'outside .text'):
                    score.score(candidate)
                originals.assert_not_called()

    def test_all_retained_original_windows_keep_exact_bytes(self):
        image = score.resolve_original(score.BASE / 'original.so').read_bytes()
        sections = score.sections(image)
        text = sections['.text']
        count = 0
        with (score.BASE / 'functions.tsv').open(encoding='utf-8') as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                if row['program'] != 'pump' or row['variant'] != 'selected':
                    continue
                start, end = int(row['original_start']), int(row['original_end'])
                offset = start - text['addr'] + text['offset']
                self.assertEqual(score.body(image, sections, start, end - start), image[offset:offset + end - start])
                count += 1
        self.assertEqual(count, 1035)


if __name__ == '__main__':
    unittest.main()
