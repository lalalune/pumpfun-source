"""Ranking caches belong to one immutable Cand and preserve rank/tie behavior."""
import difflib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import win


def reference(window, candidate, top):
    grams = win.opgrams(window['raw'])
    ranked = []
    for start, size, name in candidate.funcs:
        if .4 * window['bytes'] <= size <= 2.5 * window['bytes']:
            other = win.opgrams(candidate.fn(start, size))
            ranked.append((sum((grams & other).values()) / (sum((grams | other).values()) or 1), start, size, name))
    tokens = [x[2] for x in win.insns(window['raw'], window['start'], win.ORIG_SECS)]
    result = []
    for similarity, start, size, name in sorted(ranked, reverse=True)[:8]:
        other = [x[2] for x in win.insns(candidate.fn(start, size), start, candidate.secs)]
        result.append((difflib.SequenceMatcher(None, tokens, other, autojunk=False).ratio(), similarity, start, size, name))
    return sorted(result, reverse=True)[:top]


class CandidateIndexTests(unittest.TestCase):
    def test_rankings_and_repeated_queries(self):
        raw = b'\xb7\x00\x00\x00\x01\x00\x00\x00' * 4
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'candidate.so'
            path.write_bytes(raw * 4)
            funcs = [(0, 32, 'a'), (0, 32, 'alias'), (32, 24, 'b'), (64, 32, 'c')]
            with patch.object(win, 'sections', return_value={'.text': {'addr': 0, 'offset': 0, 'size': 128}}), patch.object(win, 'function_symbols', return_value=funcs):
                candidate = win.Cand(path)
                second = win.Cand(path)
            window = {'raw': raw, 'bytes': len(raw), 'start': 0}
            expected = reference(window, candidate, 3)
            with patch.object(win, 'opgrams', wraps=win.opgrams) as grams:
                self.assertEqual(win.best_candidates(window, candidate), expected)
                first = grams.call_count
                self.assertEqual(win.best_candidates(window, candidate), expected)
                self.assertEqual(grams.call_count - first, 1)  # original only
                self.assertEqual(first, 4)  # original + three unique ranges
            path.unlink()
            self.assertEqual(win.best_candidates(window, candidate), expected)
            self.assertEqual(second._opgrams, {})
            self.assertEqual(len(candidate._tokens), 3)

    def test_length_is_part_of_cache_identity(self):
        candidate = win.Cand.__new__(win.Cand)
        candidate.blob = b'\x95' + bytes(7) + b'\x95' + bytes(7)
        candidate.secs = {'.text': {'addr': 0, 'offset': 0, 'size': 16}}
        candidate._opgrams = {}; candidate._tokens = {}
        self.assertEqual(len(candidate.tokens(0, 8)), 1)
        self.assertEqual(len(candidate.tokens(0, 16)), 2)


if __name__ == '__main__': unittest.main()
