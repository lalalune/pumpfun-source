"""Exercise real Mayhem sell limit admission and bounded offline VM execution.

Negative limits must fail in argparse before candidate/case file access or
retained output writes. Nonnegative and omitted limits retain their case counts.
The positive controls use captured Mayhem bytes and two owned synthetic cases.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/mayhem_sell_differential.py'
ORIGINAL = ROOT / 'evidence/original/mayhem/deployed.so'
MODE = 'sell'
SELL_DRIVER = '''
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import mayhem_sell_differential as differential
differential.D = Path(sys.argv[2])
sys.argv = [differential.__file__, *sys.argv[3:]]
differential.main()
'''

class MayhemLimitTests(unittest.TestCase):
    def test_invalid_limits_fail_before_input_access_and_keep_output(self):
        with tempfile.TemporaryDirectory(prefix='mayhem-limit-admission-') as directory:
            directory = Path(directory)
            output = directory / 'retained.json'
            environment = dict(os.environ)
            environment.pop('PYTHONOPTIMIZE', None)
            for flags, value in (([], '-1'), ([], '-3'), (['-O'], '-1'), ([], 'not-a-number')):
                with self.subTest(flags=flags, value=value):
                    output.write_bytes(b'retained')
                    args = [sys.executable, '-B', *flags, str(SCRIPT), '--candidate',
                            str(directory / 'missing.so'), '--output', str(output), '--limit', value]
                    if MODE == 'buy':
                        args += ['--cases', str(directory / 'missing-cases.json')]
                    result = subprocess.run(args, cwd=ROOT, env=environment,
                                            capture_output=True, text=True, timeout=60)
                    if flags:
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertIn('Normal Python is required', result.stderr)
                    else:
                        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                        self.assertIn('argument --limit:', result.stderr)
                        if value.startswith('-'):
                            self.assertIn('--limit must not be negative', result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(output.read_bytes(), b'retained')

    def test_zero_positive_and_omitted_limits_keep_real_case_counts(self):
        work = ROOT / 'work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='mayhem-sell-limit-', dir=work) as directory:
            directory = Path(directory)
            cases = directory / 'sell-cases.json'
            cases.write_text(json.dumps({'cases': [
                {'name': 'paused-first', 'paused': 1},
                {'name': 'paused-second', 'paused': 1},
            ]}), encoding='utf-8')
            environment = dict(os.environ)
            environment.pop('PYTHONOPTIMIZE', None)
            for value, expected in (('0', 0), ('1', 1), (None, 2)):
                with self.subTest(limit=value):
                    output = directory / ('report-' + str(value) + '.json')
                    arguments = ['--candidate', str(ORIGINAL), '--output', str(output)]
                    if value is not None:
                        arguments += ['--limit', value]
                    if MODE == 'buy':
                        command = [sys.executable, '-B', str(SCRIPT), *arguments, '--cases', str(cases)]
                    else:
                        # Supply this legacy runner's existing D input with owned cases.
                        command = [sys.executable, '-B', '-c', SELL_DRIVER,
                                   str(ROOT / 'scripts'), str(directory), *arguments]
                    result = subprocess.run(command, cwd=ROOT, env=environment,
                                            capture_output=True, text=True, timeout=120)
                    self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
                    report = json.loads(output.read_text(encoding='utf-8'))
                    self.assertEqual(report['case_count'], expected)
                    self.assertEqual(len(report['cases']), expected)
                    self.assertEqual(report['signed_transactions'], 2 * expected)
                    self.assertEqual(report['mismatches'], [])
                    for row in report['cases']:
                        self.assertTrue(row['original']['signature_verified'])
                        self.assertTrue(row['candidate']['signature_verified'])

if __name__ == '__main__':
    unittest.main()
