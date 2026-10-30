"""A rebuild must not filter loaded candidate functions using a newer score."""
import contextlib
import io
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_elf_symbols import fixture
import win


class WindowListSnapshotTests(unittest.TestCase):
    def test_list_membership_and_ranking_use_the_same_candidate(self):
        # An actual captured exit window gives the replacement a real match.
        window = next(w for w in win.original_windows()
                      if w['raw'] == bytes.fromhex('9500000000000000'))
        first = fixture()
        first[424:440] = struct.pack('<BBhi', 0xb7, 0, 0, 111) * 2
        second = bytearray(first)
        second[424:432] = window['raw']
        for change in ('stable', 'replace', 'remove'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'candidate.so'
                path.write_bytes(second)
                self.assertTrue(win.score(path)[window['start']]['normalized'])
                path.write_bytes(first)
                self.assertFalse(win.score(path)[window['start']]['normalized'])
                load = win.Cand

                def rebuild_after_load(value):
                    candidate = load(value)
                    if change == 'replace':
                        replacement = path.with_suffix('.new')
                        replacement.write_bytes(second)
                        replacement.replace(path)
                    elif change == 'remove':
                        path.unlink()
                    return candidate

                output = io.StringIO()
                with patch.object(win, 'Cand', rebuild_after_load), contextlib.redirect_stdout(output):
                    win.cmd_list(SimpleNamespace(cand=path, all=False, top=10000))
                shown = {line.split()[0] for line in output.getvalue().splitlines()}
                self.assertTrue(f"{window['start']:#08x}" in shown,
                                'the replacement score hid an unmatched loaded window')
                if change != 'remove':
                    self.assertEqual(path.read_bytes(), second if change == 'replace' else first)


if __name__ == '__main__':
    unittest.main()
