"""dis.py must locate a candidate's swap_hop through the harness's current symbol reader."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
# dis.py in this folder would otherwise shadow the standard library module unittest imports.
sys.path[:] = [entry for entry in sys.path if Path(entry or '.').resolve() != HERE]

import contextlib  # noqa: E402
import io  # noqa: E402
import runpy  # noqa: E402
import unittest  # noqa: E402
from unittest import mock  # noqa: E402

ROOT = HERE.parents[3]
HARNESS = ROOT / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))
import score  # noqa: E402
import win  # noqa: E402


class CandidateDisassemblyTests(unittest.TestCase):
    def test_candidate_range_prints_function_relative_offsets(self):
        start = 0x1000
        functions = [(start, 16, 'pump8swap_hop17h0123456789abcdefE')]
        listing = {start: 'mov64 r1, r2', start + 8: 'exit'}
        stdout = io.StringIO()
        argv = ['dis.py', str(HARNESS), 'candidate.so']
        with (mock.patch.object(sys, 'argv', argv), mock.patch.object(sys, 'path', list(sys.path)),
              mock.patch.object(score, 'candidate_functions', return_value=functions),
              mock.patch.object(win, 'objdump_text', return_value=listing),
              contextlib.redirect_stdout(stdout)):
            try:
                runpy.run_path(str(HERE / 'dis.py'), run_name='__main__')
            except AttributeError as error:
                self.fail(str(error))
        self.assertEqual(stdout.getvalue().splitlines(), ['0x0 mov64 r1, r2', '0x8 exit'])


if __name__ == '__main__':
    unittest.main()
