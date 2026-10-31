"""The documented replay must start against the current shared trade fixture."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'

# Runs the unchanged replay.py with one real case, and refuses any read of the
# repository fixture the replay exists to relocate.
DRIVER = r'''
import builtins, importlib.util, runpy, sys, types
root, tool = sys.argv[1], sys.argv[2]
real_open = builtins.open
def guarded_open(path, *args, **kwargs):
    if 'curve-fresh-trades' in str(path):
        raise AssertionError('replay read the repository fixture')
    return real_open(path, *args, **kwargs)
builtins.open = guarded_open
suite = types.ModuleType('pump_v3_configured_fee_differential')
def cases():
    spec = importlib.util.spec_from_file_location(
        'real_suite', root + '/scripts/pump_v3_configured_fee_differential.py')
    real = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(real)
    suite.run = real.run
    return [next(c for c in real.cases() if c['operation'] == 'buy_v3')]
suite.cases = cases
sys.modules[suite.__name__] = suite
sys.argv = [tool] + sys.argv[3:]
runpy.run_path(tool, run_name='__main__')
'''


class ReplayStartTests(unittest.TestCase):
    def test_replay_runs_one_case_on_the_retained_fixture(self):
        with tempfile.TemporaryDirectory() as scratch:
            output = Path(scratch) / 'runtime.json.gz'
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(ROOT), str(HERE / 'replay.py'),
                 '--control', str(ORIGINAL), '--candidate', str(ORIGINAL), '--output', str(output)],
                capture_output=True, text=True, timeout=300)
            self.assertEqual(result.returncode, 0, result.stderr[-600:])
            report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(report['case_count'], 1)
        self.assertEqual((report['differences'], report['regressions']), ([], []))


if __name__ == '__main__':
    unittest.main()
