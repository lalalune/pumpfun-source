"""Historical pairings must not exempt newly matched windows from call auditing."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

LANE = Path(__file__).resolve().parents[1] / 'pump-main/lanes/callgraph-census'
sys.path.insert(0, str(LANE))
import callid_audit as audit


class CurrentMatches(unittest.TestCase):
    def test_former_pin_is_pruned_when_its_callee_does_not_match(self):
        class Image:
            def __init__(self, path, funcs):
                self.funcs, self.secs = funcs, {}
                self.original = path == Path('original.so')

            def raw(self, start):
                return b'caller00' if start in (0x100, 0x300) else (b'callee01' if self.original else b'callee02')

            def calls(self, start):
                return [(start, 0x200 if self.original else 0x400)] if start in (0x100, 0x300) else []

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            with patch.multiple(audit.C, Image=Image, ORIG_PATH=Path('original.so'),
                                PAIRS={0x100: 'historical-caller'},
                                original_windows=lambda: [{'start': s, 'bytes': 8} for s in (0x100, 0x200)],
                                candidate_functions=lambda _: [(0x300, 8, 'historical-caller'), (0x400, 8, 'callee')],
                                normalize=lambda raw, *_: raw), \
                    patch.object(sys, 'argv', ['callid_audit.py', '--cand', 'candidate.so', '--json', str(output)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                audit.main()
            result = json.loads(output.read_text())
        self.assertEqual(result['normalized_matched'], 1)
        self.assertEqual(result['bisimilar_matched'], 0)
        self.assertEqual(result['pinned_targets'], [])
        self.assertEqual(result['hidden_call_target_mismatch'][0]['window'], '0x100')

    @unittest.skipUnless(os.environ.get('CALLID_REAL_CANDIDATE'), 'set CALLID_REAL_CANDIDATE to a retained unstripped build')
    def test_retained_compiler_artifact_matches_the_official_membership_count(self):
        from original_input import resolve_original
        import score
        candidate = Path(os.environ['CALLID_REAL_CANDIDATE']).resolve()
        memberships = score.score(candidate)
        matched = {start for start, row in memberships.items() if row['normalized']}
        formerly_pinned = matched & audit.C.PAIRS.keys()
        self.assertTrue(formerly_pinned, 'artifact must exercise a now-matching historical pairing')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'audit.json'
            with patch.object(audit.C, 'ORIG_PATH', resolve_original(audit.C.ORIG_PATH)), \
                    patch.object(sys, 'argv', ['callid_audit.py', '--cand', str(candidate), '--json', str(output)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                audit.main()
            result = json.loads(output.read_text())
        self.assertEqual(result['normalized_matched'], len(matched))
        self.assertFalse(formerly_pinned & {int(row['window'], 0) for row in result['pinned_targets']})


if __name__ == '__main__':
    unittest.main()
