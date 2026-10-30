"""Real Mayhem sell_v2 CLI limit checks with bounded native-family VM controls."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/mayhem_sell_v2_differential.py'
ORIGINAL = ROOT / 'evidence/original/mayhem/deployed.so'
WSOL = 'So11111111111111111111111111111111111111112'
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
INSTRUCTIONS = (None,)

def arguments(candidate, output, cases, instruction):
    args = ['--candidate', str(candidate), '--output', str(output),
            '--cases', str(cases), '--family', 'native']
    if instruction is not None:
        args += ['--instruction', instruction]
    return args

def run(args, flags=()):
    environment = dict(os.environ)
    environment.pop('PYTHONOPTIMIZE', None)
    return subprocess.run([sys.executable, '-B', *flags, str(SCRIPT), *args],
                          cwd=ROOT, env=environment, capture_output=True,
                          text=True, timeout=120)

class MayhemLimitTests(unittest.TestCase):
    def test_invalid_limits_fail_before_input_access_and_keep_output(self):
        with tempfile.TemporaryDirectory(prefix='mayhem-limit-admission-') as directory:
            directory = Path(directory)
            output = directory / 'retained.json'
            for instruction in INSTRUCTIONS:
                for flags, value in (([], '-1'), ([], '-3'), (['-O'], '-1'), ([], 'not-a-number')):
                    with self.subTest(instruction=instruction, flags=flags, value=value):
                        output.write_bytes(b'retained')
                        args = arguments(directory / 'missing.so', output,
                                         directory / 'missing-cases.json', instruction)
                        result = run([*args, '--limit', value], flags)
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

    def test_native_zero_positive_and_default_limits_keep_real_case_counts(self):
        work = ROOT / 'work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='mayhem-sell_v2-limit-', dir=work) as directory:
            directory = Path(directory)
            cases = directory / 'cases.json'
            cases.write_text(json.dumps({'cases': [
                {'name': 'paused-first', 'paused': 1},
                {'name': 'paused-second', 'paused': 1},
            ]}), encoding='utf-8')
            for instruction in INSTRUCTIONS:
                for value, expected in (('0', 0), ('1', 1), (None, 2)):
                    with self.subTest(instruction=instruction, limit=value):
                        output = directory / ('report-' + str(instruction) + '-' + str(value) + '.json')
                        args = arguments(ORIGINAL, output, cases, instruction)
                        if value is not None:
                            args += ['--limit', value]
                        result = run(args)
                        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
                        report = json.loads(output.read_text(encoding='utf-8'))
                        self.assertEqual(report['case_count'], expected)
                        self.assertEqual(len(report['cases']), expected)
                        self.assertEqual(report['signed_transactions'], 2 * expected)
                        self.assertEqual(report['mismatches'], [])
                        for row in report['cases']:
                            self.assertFalse(row['case']['token_quote'])
                            self.assertFalse(row['case']['quote_token22'])
                            for side in ('original', 'candidate'):
                                self.assertTrue(row[side]['signature_verified'])
                                self.assertEqual(row[side]['before'][WSOL]['owner'], TOKEN)

if __name__ == '__main__':
    unittest.main()
