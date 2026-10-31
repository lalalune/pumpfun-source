"""A harness that cannot load is an infrastructure error, never a valid non-match."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import experiment_runner

ORACLE = Path(__file__).with_name('match_oracle.py')


def command(root):
    return [sys.executable, '-B', str(ORACLE), '--source', str(root / 'crate'), '--work', str(root / 'work'),
            '--out', str(root / 'out'), '--sdk', str(root / 'sdk'), '--hybrid', str(root / 'hybrid'),
            '--window', '0x14f4e0']


class MatchOracleImportFailureTests(unittest.TestCase):
    def test_unloadable_builder_exits_two(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(command(Path(directory)), capture_output=True, text=True, timeout=30,
                                    env=dict(os.environ, PUMP_BUILD_SLOTS='two'))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('match oracle error', result.stderr)

    def test_experiment_records_an_error_instead_of_a_failed_predicate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'crate').mkdir()
            with patch.dict(os.environ, {'PUMP_BUILD_SLOTS': 'two'}):
                record = experiment_runner.run_trial(root / 'crate', command(root), root / 'trial', timeout=30)
        self.assertEqual(record['status'], 'error')
        self.assertEqual(record['returncode'], 2)


if __name__ == '__main__':
    unittest.main()
