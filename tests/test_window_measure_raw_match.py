import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import window_measure  # noqa: E402


class FakeElf:
    """Two candidate functions share a normalized window; only the second is raw-equal."""

    def __init__(self, path):
        name = Path(path).name
        call = lambda imm: bytes([0x85, 0x10, 0, 0, imm, 0, 0, 0])
        if name == 'original':
            self.b = call(2)
            self.entries, self.hi, self.funcs = [0], 8, []
        else:
            self.b = call(1) + call(2)
            self.entries, self.hi = [0, 8], 16
            self.funcs = [{'name': 'first', 'start': 0, 'size': 8},
                          {'name': 'second', 'start': 8, 'size': 8}]
        norm = bytearray(self.b)
        for at in range(0, len(norm), 8):
            norm[at + 4:at + 8] = bytes(4)
        self.normalized = bytes(norm)

    def pattern(self, start, size):
        return []


class WindowMeasureRawMatchTest(unittest.TestCase):
    def test_reported_match_is_the_raw_equal_function(self):
        with mock.patch.object(window_measure, '_elf_class', return_value=FakeElf):
            rows = window_measure.measure('original', 'candidate')
        self.assertEqual(rows, [{'original': '0x0', 'bytes': 8, 'match': 'second', 'raw': True}])

    def test_normalized_only_match_keeps_first_function(self):
        class NoRaw(FakeElf):
            def __init__(self, path):
                super().__init__(path)
                if Path(path).name == 'original':
                    self.b = bytes([0x85, 0x10, 0, 0, 9, 0, 0, 0])
        with mock.patch.object(window_measure, '_elf_class', return_value=NoRaw):
            rows = window_measure.measure('original', 'candidate')
        self.assertEqual(rows[0]['match'], 'first')
        self.assertFalse(rows[0]['raw'])


if __name__ == '__main__':
    unittest.main()
