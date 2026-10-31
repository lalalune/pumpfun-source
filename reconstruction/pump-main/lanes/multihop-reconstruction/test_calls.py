"""calls.py must locate a candidate's swap_hop through the harness's current symbol reader."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
# dis.py and cmp.py in this folder would otherwise shadow the standard library modules.
sys.path[:] = [entry for entry in sys.path if Path(entry or '.').resolve() != HERE]

import contextlib  # noqa: E402
import io  # noqa: E402
import runpy  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from unittest import mock  # noqa: E402

ROOT = HERE.parents[3]
HARNESS = ROOT / 'reconstruction/harness'
sys.path.insert(0, str(HARNESS))
import coords  # noqa: E402
import score  # noqa: E402
import win  # noqa: E402


class CandidateCallListTests(unittest.TestCase):
    def test_candidate_calls_print_callee_names_and_lines(self):
        start = 0x1000
        functions = [(start, 16, 'pump8swap_hop17h0123456789abcdefE'),
                     (0x2000, 8, 'pump6callee17h0123456789abcdefE')]
        listing = {start: 'call 0x1ff', start + 8: 'exit'}
        stdout = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes(b'')
            argv = ['calls.py', str(HARNESS), str(candidate)]
            with (mock.patch.object(sys, 'argv', argv), mock.patch.object(sys, 'path', list(sys.path)),
                  mock.patch.object(score, 'candidate_functions', return_value=functions),
                  mock.patch.object(win, 'objdump_text', return_value=listing),
                  mock.patch.object(coords, 'sections', return_value={}),
                  mock.patch.object(coords, 'cand_sites', return_value=[{'line': 42}]),
                  contextlib.redirect_stdout(stdout)):
                try:
                    runpy.run_path(str(HERE / 'calls.py'), run_name='__main__')
                except AttributeError as error:
                    self.fail(str(error))
        self.assertEqual(stdout.getvalue().splitlines(), ['0x0 0x2000 pump6callee [42]'])


if __name__ == '__main__':
    unittest.main()
