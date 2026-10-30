import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import experiment_runner as runner  # noqa: E402


class MatrixOverlapAdmissionTests(unittest.TestCase):
    def assert_refused_before_any_trial(self, root, overlapping):
        (root / 'clean').mkdir(exist_ok=True)
        overlapping.mkdir(parents=True, exist_ok=True)
        rows = [{'name': 'first', 'source': str(root / 'clean'), 'command': [sys.executable, '-c', 'pass']},
                {'name': 'second', 'source': str(overlapping), 'command': [sys.executable, '-c', 'pass']}]
        matrix = root / 'matrix.json'
        matrix.write_text(json.dumps(rows), encoding='utf-8')
        stderr = io.StringIO()
        with patch.object(sys, 'argv', ['runner', str(matrix), '--out', str(root / 'out')]), \
             patch.object(runner, 'run_trial', return_value={'status': 'pass'}) as trial, \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as error:
                runner.main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('invalid experiment matrix', stderr.getvalue())
        trial.assert_not_called()

    def test_later_source_containing_the_output_runs_no_earlier_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assert_refused_before_any_trial(root, root)

    def test_later_source_inside_its_trial_output_runs_no_earlier_trial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.assert_refused_before_any_trial(root, root / 'out/second/source')

    def test_separate_trees_still_reach_the_trial_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'source').mkdir()
            row = {'name': 'valid', 'source': str(root / 'source'), 'command': [sys.executable, '-c', 'pass']}
            matrix = root / 'matrix.json'
            matrix.write_text(json.dumps([row]), encoding='utf-8')
            with patch.object(sys, 'argv', ['runner', str(matrix), '--out', str(root / 'out')]), \
                 patch.object(runner, 'run_trial', return_value={'status': 'pass'}) as trial, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            trial.assert_called_once()


if __name__ == '__main__':
    unittest.main()
