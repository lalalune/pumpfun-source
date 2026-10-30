"""Frozen two-curve assertions cannot silently disappear in optimized Python."""
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MESSAGE = 'Two-curve replay requires normal Python; do not use -O or PYTHONOPTIMIZE'
DRIVER = '''
from pathlib import Path
import runpy
import subprocess
import sys
def forbidden(*args, **kwargs):
    raise RuntimeError('guard reached an external command or filesystem mutation')
subprocess.run = forbidden
Path.mkdir = forbidden
runpy.run_path(sys.argv[1], run_name='__main__')
'''


class TwoCurveOptimizationGuardTests(unittest.TestCase):
    def check_rejected_before_work(self, relative):
        result = subprocess.run(
            [sys.executable, '-O', '-B', '-c', DRIVER, str(ROOT / relative)],
            capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(MESSAGE, result.stderr)
        self.assertNotIn('guard reached an external command or filesystem mutation', result.stderr)
        self.assertEqual(result.stdout, '')

    def test_maintained_replay_rejects_optimization(self):
        self.check_rejected_before_work('scripts/pump_tokenkeg_two_curve_differential.py')

    def test_producer_replay_rejects_optimization(self):
        self.check_rejected_before_work('research/pump-two-curve-inputs/reproduce.py')


if __name__ == '__main__':
    unittest.main()
