"""Exact instruction edit-distance regressions; no compiler or VM required."""
import importlib.util
from pathlib import Path
import struct
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('distance_sell_score', HERE / 'sell_score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


def tokens(values):
    # Complete, valid mov64-immediate instructions. Constants are preserved by
    # the real listing and token normalization, not supplied as fake token rows.
    raw = b''.join(struct.pack('<BBhi', 0xb7, 0, 0, value) for value in values)
    image = type('Image', (), {'b': raw})()
    return score.normalized_tokens(score.listing(image, 0, len(raw)))


class AlignmentDistanceTests(unittest.TestCase):
    def test_one_substitution_between_repeated_instructions_costs_one(self):
        self.assertEqual(score.alignment_distance(tokens([0, 0, 0]), tokens([0, 1, 0])), 1)
        self.assertEqual(score.alignment_distance(tokens([0, 1, 0]), tokens([0, 0, 0])), 1)

    def test_two_substitutions_beat_a_longer_matching_block_alignment(self):
        self.assertEqual(score.alignment_distance(tokens([0, 0, 0, 0]), tokens([0, 1, 1, 0])), 2)

    def test_empty_identical_and_indel_controls(self):
        a = tokens([0, 1, 2])
        for left, right, expected in (([], [], 0), (a, [], 3), ([], a, 3),
                                      (a, a, 0), (a, tokens([0, 2]), 1),
                                      (tokens([0, 2]), a, 1), (a, tokens([3, 4, 5]), 3)):
            with self.subTest(left=left, right=right):
                self.assertEqual(score.alignment_distance(left, right), expected)


if __name__ == '__main__':
    unittest.main()
