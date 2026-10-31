"""blocksim.py must not report success when --sym selects no candidate function."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('census_blocksim', HERE / 'blocksim.py')
blocksim = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(blocksim)

EXIT = (b'\x95' + bytes(7))
WINDOW = {'start': 0x1000, 'bytes': 8, 'raw': EXIT}


class FakeCandidate:
    funcs = [(0x2000, 8, 'pump5other17h0123456789abcdefE')]
    secs = {}

    def __init__(self, path):
        self.path = path

    def fn(self, start, size):
        return EXIT


class SymbolSelectionTests(unittest.TestCase):
    def run_main(self, pattern):
        argv = ['blocksim.py', 'candidate.so', '0x1000', '--sym', pattern]
        stdout = io.StringIO()
        with (mock.patch.object(sys, 'argv', argv),
              mock.patch.object(blocksim, 'original_windows', return_value=[WINDOW]),
              mock.patch.object(blocksim, 'Cand', FakeCandidate),
              mock.patch.object(blocksim, 'demangle', side_effect=lambda name: name),
              mock.patch.object(blocksim, 'normalize', side_effect=lambda raw, addr, secs: raw),
              contextlib.redirect_stdout(stdout)):
            try:
                blocksim.main()
            except SystemExit as stop:
                return stop.code, stdout.getvalue()
        return 0, stdout.getvalue()

    def test_matching_symbol_prints_one_comparison(self):
        code, output = self.run_main('other')
        self.assertEqual(code, 0)
        self.assertEqual(output.count("'block_jaccard'"), 1)

    def test_unmatched_symbol_is_a_failure(self):
        code, output = self.run_main('no_such_function')
        self.assertEqual(output, '')
        self.assertNotIn(code, (0, None), 'an unmatched --sym exited successfully')
        self.assertIn('no_such_function', str(code))


if __name__ == '__main__':
    unittest.main()
