"""reconstruction/harness/score.py must not fall back to an empty baseline.

Against an empty baseline every matched window is a "gain" and `losses` is always
empty, which is exactly the signal the acceptance rule reads. These tests exercise
only the CLI's baseline handling; `score.score` is replaced so no SDK, objdump or
candidate build is needed.

Run from the repository root: python3 -I -B -m unittest tests/test_score_baseline.py
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCORE_PY = ROOT / 'reconstruction' / 'harness' / 'score.py'
DEFAULT_BASELINE = ROOT / 'reconstruction' / 'pump-main' / 'baseline' / 'score.json'

# Two windows: 0x100 matched in the fake candidate, 0x200 not matched.
FAKE_SCORE = {
    0x100: {'normalized': True, 'raw': True, 'symbols': ['a'], 'bytes': 8},
    0x200: {'normalized': False, 'raw': False, 'symbols': [], 'bytes': 16},
}
# Baseline where both were matched, so 0x200 is a loss and nothing is a gain.
BASELINE = {'windows': {
    '256': {'normalized': True, 'raw': True, 'bytes': 8},
    '512': {'normalized': True, 'raw': False, 'bytes': 16},
}}


def load_score_module():
    if str(SCORE_PY.parent) not in sys.path:
        sys.path.insert(0, str(SCORE_PY.parent))  # score.py imports llvm_tools from its own directory
    spec = importlib.util.spec_from_file_location('score_under_test', SCORE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ScoreBaselineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.candidate = tmp / 'cand.so'
        self.candidate.write_bytes(b'\x7fELF fake candidate')
        self.baseline = tmp / 'baseline.json'
        self.baseline.write_text(json.dumps(BASELINE))
        self.mod = load_score_module()

    def run_main(self, *argv):
        out = io.StringIO()
        with mock.patch.object(self.mod, 'score_with_hash', return_value=(dict(FAKE_SCORE), '0'*64)), \
                mock.patch.object(sys, 'argv', ['score.py', str(self.candidate), *argv]), \
                contextlib.redirect_stdout(out):
            self.mod.main()
        return json.loads(out.getvalue())

    def test_default_baseline_is_the_checked_in_pump_main_baseline(self):
        self.assertEqual(Path(self.mod.DEFAULT_BASELINE), DEFAULT_BASELINE)
        self.assertTrue(DEFAULT_BASELINE.is_file(), 'default baseline must exist in the checkout')

    def test_explicit_baseline_reports_losses(self):
        summary = self.run_main('--baseline', str(self.baseline), '--quiet')
        self.assertEqual(summary['gains'], [])
        self.assertEqual(summary['losses'], ['0x200'])
        self.assertEqual(summary['raw_losses'], [])

    def test_missing_baseline_is_an_error_not_an_empty_baseline(self):
        missing = Path(self.tmp.name) / 'typo.json'
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(self.mod, 'score_with_hash', return_value=(dict(FAKE_SCORE), '0'*64)) as scored, \
                mock.patch.object(sys, 'argv', ['score.py', str(self.candidate), '--baseline', str(missing)]), \
                contextlib.redirect_stderr(err), contextlib.redirect_stdout(out), \
                self.assertRaises(SystemExit) as cm:
            self.mod.main()
        # A missing baseline is a usage error: exit 2, name the path on stderr, print no summary.
        self.assertEqual(cm.exception.code, 2)
        self.assertIn(str(missing), err.getvalue())
        self.assertIn('--no-baseline', err.getvalue())
        self.assertEqual(out.getvalue(), '')
        scored.assert_not_called()

    def test_no_baseline_opt_out_reports_all_matches_as_gains(self):
        summary = self.run_main('--no-baseline', '--quiet')
        self.assertEqual(summary['gains'], ['0x100'])
        self.assertEqual(summary['losses'], [])


if __name__ == '__main__':
    unittest.main()
