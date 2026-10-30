"""Reject triage reports that alias an input file.

Sibling of open #2236 (coords.py, candidate only) and of score.py's own
report destination check: triage.py wrote its --json report with a plain
write_text and no destination check at all, so --json pointing at the
candidate (or, by the same write, at the saved original or the window
inventory) truncated that input after the analysis read it. The guard
runs before any read and covers the candidate, the saved original, and
the inventory, mirroring score.py's input set.
"""
import contextlib, hashlib, importlib.util, io, os, sys, tempfile, unittest
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
SPEC = importlib.util.spec_from_file_location('window_triage_destination', H / 'triage.py')
triage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(triage)


def run_alias(alias_kind):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cand = tmp / 'cand.so'
        cand.write_bytes(b'ELF')
        before = hashlib.sha256(cand.read_bytes()).hexdigest()
        if alias_kind == 'same':
            out = cand
        elif alias_kind == 'symlink':
            out = tmp / 'triage.json'
            try:
                os.symlink(cand, out)
            except (OSError, NotImplementedError, AttributeError) as error:
                raise unittest.SkipTest(f'creating links is not permitted: {error}')
        else:
            out = tmp / 'triage.json'
            os.link(cand, out)
        # Stub the analysis so only the destination guard is exercised.
        triage.sections = lambda blob: {'.text': {'addr': 0x1000, 'offset': 0, 'size': 8}}
        triage.score = lambda p: {0x1000: {'normalized': False}}
        triage.candidate_functions = lambda p: [(0x1000, 8, '_ZN4testE')]
        triage.original_windows = lambda: [{'start': 0x1000, 'bytes': 8, 'raw': b'ELFELFEL'}]
        triage.sites = lambda blob, secs, start, raw: []
        triage.normalize = lambda raw, addr, secs: raw
        triage.body = lambda blob, secs, addr, size: b'ELFELFEL'
        triage.demangle = lambda name: name
        argv = sys.argv
        sys.argv = ['triage.py', '--cand', str(cand), '--json', str(out)]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with unittest.TestCase().assertRaises(SystemExit) as caught:
                    triage.main()
        finally:
            sys.argv = argv
        if caught.exception.code != 2:
            raise AssertionError(f'expected exit 2, got {caught.exception.code}')
        if hashlib.sha256(cand.read_bytes()).hexdigest() != before:
            raise AssertionError('candidate was modified despite the alias')


def run_ok():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        cand = tmp / 'cand.so'
        cand.write_bytes(b'ELF')
        out = tmp / 'triage.json'
        triage.sections = lambda blob: {'.text': {'addr': 0x1000, 'offset': 0, 'size': 8}}
        triage.score = lambda p: {0x1000: {'normalized': False}}
        triage.candidate_functions = lambda p: [(0x1000, 8, '_ZN4testE')]
        triage.original_windows = lambda: [{'start': 0x1000, 'bytes': 8, 'raw': b'ELFELFEL'}]
        triage.sites = lambda blob, secs, start, raw: []
        triage.normalize = lambda raw, addr, secs: raw
        triage.body = lambda blob, secs, addr, size: b'ELFELFEL'
        triage.demangle = lambda name: name
        argv = sys.argv
        sys.argv = ['triage.py', '--cand', str(cand), '--json', str(out)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                triage.main()
        finally:
            sys.argv = argv
        return out.exists()


class TriageReportDestinationTests(unittest.TestCase):
    def test_report_destination_cannot_alias_candidate(self):
        for alias_kind in ('same', 'symlink', 'hardlink'):
            with self.subTest(alias_kind=alias_kind):
                run_alias(alias_kind)

    def test_distinct_destination_still_writes(self):
        self.assertTrue(run_ok())


if __name__ == '__main__':
    unittest.main(verbosity=2)
