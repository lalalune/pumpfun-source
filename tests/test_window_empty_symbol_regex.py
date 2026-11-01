"""Explicit regex selection is independent of whether its string is truthy."""
import contextlib
import gzip
import hashlib
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import win


class EmptySymbolRegexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.image = Path(cls.temporary.name) / 'retained-symbols.so'
        data = gzip.decompress((ROOT / 'research/pump-multihop-token-quote-20261029/build/parent/symbols.so.gz').read_bytes())
        if hashlib.sha256(data).hexdigest() != 'e1c9bdc3b248d41ebd73c1f8d0d2756edf95eafa178b8aed4a8ae0715649705a':
            raise AssertionError('retained input changed')
        cls.image.write_bytes(data)

    def show(self, pattern):
        args = SimpleNamespace(start='0x120', cand=self.image, sym=pattern, context=3, full=False)
        output = io.StringIO()
        # Selection, ELF parsing, ranking and diffing are real. Only assembly
        # rendering is omitted so this focused regression needs no installed SDK.
        # The public probe separately runs the complete CLI with official objdump.
        with patch.object(win, 'objdump_text', return_value={}), contextlib.redirect_stdout(output):
            win.cmd_show(args)
        return output.getvalue()

    def test_empty_and_equivalent_regex_select_all_retained_functions(self):
        empty, equivalent = self.show(''), self.show('(?:)')
        self.assertEqual(empty, equivalent)
        self.assertEqual(sum(line.startswith('  cand ') for line in empty.splitlines()), 1090)

    def test_absent_and_restrictive_filters_keep_their_scopes(self):
        for pattern, expected in ((None, 3), ('^custom_panic$', 1)):
            with self.subTest(pattern=pattern):
                output = self.show(pattern)
                self.assertEqual(sum(line.startswith('  cand ') for line in output.splitlines()), expected)

    def test_nonmatching_filter_remains_an_empty_search_error(self):
        with self.assertRaisesRegex(SystemExit, 'no candidate symbol matches'):
            self.show('^no_such_retained_function$')


if __name__ == '__main__':
    unittest.main()
