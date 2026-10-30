"""reconstruction/harness/win.py must reject unknown window starts cleanly.

`win.py show` and `win.py orig` looked the address up with a bare `next(...)`, so a
typo or a non-window address ended in an uncaught StopIteration traceback, and a
non-numeric address in a ValueError traceback. They now exit 2 with a stderr message.
The window table comes from the committed original.so and functions.tsv, so no SDK,
objdump or candidate build is needed; disassembly is replaced in the valid-start test.

Run from the repository root: python3 -I -B tests/test_win_unknown_window.py
"""
import contextlib
import importlib.util
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / 'reconstruction' / 'harness'
WIN_PY = HARNESS / 'win.py'
VALID_START = 0x14f4e0  # README example window


def load_win_module():
    sys.path.insert(0, str(HARNESS))
    spec = importlib.util.spec_from_file_location('win_under_test', WIN_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_cli(*args):
    return subprocess.run([sys.executable, '-I', '-B', str(WIN_PY), *args],
                          cwd=ROOT, capture_output=True, text=True)


class WinUnknownWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.win = load_win_module()

    def assert_clean_error(self, result, needle):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(needle, result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_orig_rejects_non_window_start(self):
        self.assert_clean_error(run_cli('orig', '0x14f4e1'), '0x14f4e1 is not an original window start')

    def test_show_rejects_non_window_start(self):
        self.assert_clean_error(run_cli('show', '0x1', '--cand', '/dev/null'), '0x1 is not an original window start')

    def test_non_numeric_address(self):
        for cmd in (['orig', 'nope'], ['show', 'nope', '--cand', '/dev/null']):
            with self.subTest(cmd=cmd):
                self.assert_clean_error(run_cli(*cmd), "'nope' is not a numeric address")

    def test_valid_start_still_resolves(self):
        st, w = self.win.find_window(hex(VALID_START))
        self.assertEqual(st, VALID_START)
        self.assertEqual(w['start'], VALID_START)
        self.assertGreater(w['bytes'], 0)

    def test_orig_valid_start_reaches_disassembly(self):
        calls = []

        def fake_objdump(path, start, end):
            calls.append((start, end))
            return {start: 'fake insn'}

        out = io.StringIO()
        with mock.patch.object(self.win, 'objdump_text', fake_objdump), contextlib.redirect_stdout(out):
            self.win.cmd_orig(mock.Mock(start=hex(VALID_START)))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], VALID_START)
        self.assertIn('fake insn', out.getvalue())


if __name__ == '__main__':
    unittest.main()
