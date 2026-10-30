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


def runner_module():
    spec = importlib.util.spec_from_file_location('matrix_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}): spec.loader.exec_module(module)
    return module


class MatrixAdmissionTests(unittest.TestCase):
    def test_invalid_rows_and_fields_fail_before_any_trial(self):
        runner = runner_module()
        cases = [[None], [42], ['row'], [{'name':'valid'}],
                 [{'name':'valid', 'source':None, 'command':[sys.executable]}],
                 [{'name':'valid', 'source':'.', 'command':[], 'inputs':'wrong'}]]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            matrix = root / 'matrix.json'
            out = root / 'out'
            for rows in cases:
                matrix.write_text(json.dumps(rows), encoding='utf-8')
                stderr = io.StringIO()
                with self.subTest(rows=rows), patch.object(sys, 'argv', ['runner', str(matrix), '--out', str(out)]), \
                     patch.object(runner, 'run_trial') as trial, contextlib.redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as error: runner.main()
                    self.assertEqual(error.exception.code, 2)
                    self.assertIn('invalid experiment matrix', stderr.getvalue())
                    trial.assert_not_called()
                    self.assertFalse(out.exists())

    def test_boolean_deadline_is_not_a_numeric_duration(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError): runner.identity(directory, [sys.executable], [], True)

    def test_valid_matrix_reaches_the_trial_boundary(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            matrix = root / 'matrix.json'
            row = {'name':'valid', 'source':str(source), 'command':[sys.executable, '-c', 'pass'],
                   'inputs':[], 'timeout':0.5}
            matrix.write_text(json.dumps([row]), encoding='utf-8')
            with patch.object(sys, 'argv', ['runner', str(matrix), '--out', str(root/'out')]), \
                 patch.object(runner, 'run_trial', return_value={'status':'pass'}) as trial, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
                trial.assert_called_once_with(str(source), row['command'], root/'out/valid', [], 0.5)


if __name__ == '__main__': unittest.main()
