"""Clones with one opcode stream must not push an exact body off the shortlist.

The opcode 3-gram score ignores immediates, so generated clones tie exactly. The
descending sort then cut them by address, and an exact body at a low address never
reached the instruction comparison. The captured Pump image has 47 such windows.
"""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import win


def body(immediate):
    return (struct.pack('<BBhi', 0xb7, 1, 0, immediate)
            + struct.pack('<BBhi', 0xb7, 2, 0, 2)
            + struct.pack('<BBhi', 0xb7, 3, 0, 3)
            + struct.pack('<BBhi', 0x95, 0, 0, 0))


class Clones:
    def __init__(self, bodies):
        self.bodies = bodies
        self.funcs = [(start, len(raw), f'fn_{start:x}') for start, raw in bodies.items()]

    def grams(self, start, size):
        return win.opgrams(self.bodies[start])

    def tokens(self, start, size):
        return tuple(row[2] for row in win.insns(self.bodies[start], start, win.ORIG_SECS))


class CandidateCloneTieTests(unittest.TestCase):
    window = {'start': 0x1000, 'bytes': 32, 'raw': body(1)}

    def test_exact_body_at_the_lowest_address_outranks_tied_clones(self):
        clones = {0x2000 + index * 32: body(100 + index) for index in range(12)}
        candidate = Clones({0x1000: body(1), **clones})
        ratio, _, start, _, _ = win.best_candidates(self.window, candidate, 1)[0]
        self.assertEqual((ratio, start), (1.0, 0x1000))

    def test_lower_coarse_scores_stay_outside_the_shortlist(self):
        clones = {0x2000 + index * 32: body(100 + index) for index in range(8)}
        different = struct.pack('<BBhi', 0x07, 1, 0, 1) * 3 + body(1)[24:]
        candidate = Clones({0x1000: different, **clones})
        calls = []
        tokens = candidate.tokens
        candidate.tokens = lambda start, size: calls.append(start) or tokens(start, size)
        win.best_candidates(self.window, candidate, 1)
        self.assertNotIn(0x1000, calls)


if __name__ == '__main__':
    unittest.main()
