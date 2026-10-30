"""The diagnostic candidate search must honor a requested limit above eight."""
import struct
from types import SimpleNamespace
import unittest

from win import Cand, best_candidates


class CandidateLimitTests(unittest.TestCase):
    def setUp(self):
        raw = b''.join(struct.pack('<BBhi', op, 0, 0, imm)
                       for op, imm in ((0xb7, 1), (0x07, 2), (0x95, 0)))
        self.window = {'start': 0, 'bytes': len(raw), 'raw': raw}
        self.candidate = Cand.__new__(Cand)
        self.candidate.__dict__.update(
            _opgrams={}, _tokens={}, funcs=[(i * 32, len(raw), f'fn_{i}') for i in range(12)],
            fn=lambda _start, _size: raw, secs={})

    def test_requested_ten_candidates_are_returned(self):
        self.assertEqual(len(best_candidates(self.window, self.candidate, 10)), 10)

    def test_limit_larger_than_available_returns_all(self):
        self.assertEqual(len(best_candidates(self.window, self.candidate, 20)), 12)

    def test_default_ranking_and_limit_are_preserved(self):
        rows = best_candidates(self.window, self.candidate)
        self.assertEqual(len(rows), 3)
        self.assertEqual([row[2] for row in rows], [352, 320, 288])
        self.assertTrue(all(row[0] == 1 for row in rows))

    def test_no_eligible_candidates(self):
        self.candidate.funcs = []
        self.assertEqual(best_candidates(self.window, self.candidate, 20), [])


if __name__ == '__main__':
    unittest.main()
