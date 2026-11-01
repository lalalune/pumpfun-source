import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


def runner_module():
    spec = importlib.util.spec_from_file_location('retained_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    lock = types.ModuleType('fcntl')
    lock.flock = Mock()
    lock.LOCK_EX = 2
    # Serial cache admission only; POSIX lock semantics are outside this test.
    with patch.dict(sys.modules, {'fcntl': lock}): spec.loader.exec_module(module)
    return module


class RetainedInputsTests(unittest.TestCase):
    def exercise(self, mutation):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            (source / 'lib.rs').write_bytes(b'original source')
            destination = root / 'trials'
            attempt = destination / 'attempt-synthetic'
            attempt.mkdir(parents=True)
            shutil.copytree(source, attempt / 'source')
            (attempt / 'output').mkdir()
            for name in ('stdout.log', 'stderr.log'): (attempt / name).write_bytes(b'')
            command = [sys.executable, '-c', 'pass']
            admission = runner.identity(source, command, [], 300)
            record = {'schema': 'experiment-result-v1', 'returncode': 0, 'reason': None,
                      'key': runner.digest(json.dumps(admission, sort_keys=True).encode()),
                      'attempt': attempt.name, 'status': 'pass', 'inputs': admission,
                      'artifacts': runner.artifacts(attempt)}
            (destination / 'latest.json').write_text(json.dumps(record), encoding='utf-8')
            mutation(attempt)
            with patch.object(runner.subprocess, 'Popen', side_effect=RuntimeError('fresh trial required')) as popen:
                if mutation is untouched:
                    self.assertTrue(runner.run_trial(source, command, destination)['reused'])
                    popen.assert_not_called()
                else:
                    with self.assertRaisesRegex(RuntimeError, 'fresh trial required'):
                        runner.run_trial(source, command, destination)
                    popen.assert_called_once()

    def test_changed_retained_source_requires_a_new_trial(self):
        self.exercise(lambda attempt: (attempt / 'source/lib.rs').write_bytes(b'changed source'))

    def test_missing_retained_output_requires_a_new_trial(self):
        self.exercise(lambda attempt: (attempt / 'output').rmdir())

    def test_untouched_retained_inputs_reuse_without_launch(self):
        self.exercise(untouched)


def untouched(attempt): pass


if __name__ == '__main__': unittest.main()
