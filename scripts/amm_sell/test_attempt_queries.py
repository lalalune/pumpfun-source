"""Read real temporary ledger files through the attempt-query CLI entrypoint."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sell_score import SCORE_VERSION

# Baseline imports fcntl even for read-only queries. These tests never invoke
# locking or the note writer; the module placeholder only permits that import.
with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}):
    spec = importlib.util.spec_from_file_location('query_attempts', HERE / 'attempts.py')
    queries = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(queries)


def entry(lane, *, version=SCORE_VERSION, raw_loss=0, normalized_loss=0,
          distance=10, size=9024):
    return {'schema': 'amm-sell-attempt-v1', 'lane': lane, 'approach': 'probe',
            'status': 'scored', 'hypothesis': 'synthetic ledger query control',
            'metrics': {'score_version': version, 'lost_windows_count': raw_loss,
                        'lost_windows_normalized_count': normalized_loss,
                        'sell_raw_equal': False, 'sell_size': size,
                        'align_distance': distance, 'slot_diffs': 20}}


class AttemptQueryTests(unittest.TestCase):
    def query(self, rows, *arguments):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'ATTEMPTS.jsonl'
            log.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            before = log.read_bytes()
            output = io.StringIO()
            with patch.object(queries, 'LOG', log), \
                    patch.object(sys, 'argv', ['attempts.py', *arguments]), \
                    contextlib.redirect_stdout(output):
                queries.main()
            self.assertEqual(log.read_bytes(), before)
            return output.getvalue()

    def test_best_does_not_compare_incompatible_metric_versions(self):
        rows = [entry('current', distance=10),
                entry('historical', version=SCORE_VERSION - 1, distance=0),
                entry('unversioned', version=None, distance=0)]
        result = self.query(rows, 'best')
        self.assertIn('current/probe', result)
        self.assertNotIn('historical/probe', result)
        self.assertNotIn('unversioned/probe', result)

    def test_best_treats_only_normalized_losses_as_regressions(self):
        # A legitimate sell-size change shifts every later window, inflating the
        # RAW lost_windows_count while lost_windows_normalized_count stays 0 (no
        # function actually changed; see sell_score.py). try_sell.rank() and the
        # README define a loss as lost_windows_normalized_count != 0, so `best`
        # must surface the shifted-but-non-losing attempt and drop the one whose
        # normalized windows truly regressed.
        rows = [entry('shifted', raw_loss=3, normalized_loss=0),
                entry('regressed', raw_loss=0, normalized_loss=2)]
        result = self.query(rows, 'best')
        self.assertIn('shifted/probe', result)
        self.assertNotIn('regressed/probe', result)

    def test_explicit_historical_version_is_ranked_separately(self):
        result = self.query([entry('current'),
                             entry('historical', version=SCORE_VERSION - 1)],
                            'best', '--score-version', str(SCORE_VERSION - 1))
        self.assertIn('historical/probe', result)
        self.assertNotIn('current/probe', result)

    def test_summary_uses_the_current_metric_version(self):
        result = self.query([entry('valid'),
                             entry('old', version=SCORE_VERSION - 1, distance=0)], 'summary')
        self.assertIn('2 builds, 0 notes', result)
        self.assertIn('valid/probe scored', result)
        self.assertNotIn('old/probe scored', result)

    def test_usage_documents_every_accepted_note_kind(self):
        # The module docstring is the argparse description shown by --help, so a
        # --kind value the CLI accepts but the usage omits is a help/behavior
        # contradiction. Guard every accepted kind against that drift.
        for kind in queries.NOTE_KINDS:
            self.assertIn(kind, queries.__doc__)

    def test_approach_statistics_keep_versions_separate(self):
        result = self.query([entry('current', distance=10),
                             entry('historical', version=SCORE_VERSION - 1, distance=0)],
                            'approaches')
        self.assertEqual(len(result.splitlines()), 2)
        self.assertIn(f'score_version={SCORE_VERSION} n=   1 best_dist=10', result)
        self.assertIn(f'score_version={SCORE_VERSION - 1} n=   1 best_dist=0', result)


if __name__ == '__main__':
    unittest.main()
