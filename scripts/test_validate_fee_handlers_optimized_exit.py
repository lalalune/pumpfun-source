#!/usr/bin/env python3
"""Fees query handlers must not run with optimized Python.

scripts/validate_fee_handlers.py gated its exit status on
`assert not failures`. `python -O`/`-OO` and PYTHONOPTIMIZE strip asserts,
so a candidate that mismatched every case still exited 0. The candidate
here is a real program that is not Pump Fees: the captured Mayhem
deployment loaded at the Fees address. Every case mismatches.
The captured Fees original is the control and must still pass.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'validate_fee_handlers.py'
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
OTHER_PROGRAM = ROOT / 'evidence/original/mayhem/deployed.so'


def run(script, candidate, flags, output, pythonoptimize=None):
    env = dict(os.environ)
    env.pop('PYTHONOPTIMIZE', None)
    if pythonoptimize is not None:
        env['PYTHONOPTIMIZE'] = pythonoptimize
    return subprocess.run(
        [sys.executable, *flags, '-B', str(ROOT / 'scripts' / script),
         '--candidate', str(candidate), '--output', str(output)],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')


class OptimizedExitTests(unittest.TestCase):
    def test_optimized_modes_are_rejected_before_work(self):
        with tempfile.TemporaryDirectory() as temp:
            for flags, pythonoptimize in (
                    (['-O'], None), (['-OO'], None), ([], '1'), ([], '2')):
                with self.subTest(flags=flags, pythonoptimize=pythonoptimize):
                    output = Path(temp) / (SCRIPT + ''.join(flags) + '.json')
                    result = run(SCRIPT, OTHER_PROGRAM, flags, output,
                                 pythonoptimize)
                    self.assertNotEqual(result.returncode, 0,
                                        result.stdout[-300:])
                    self.assertIn('Normal Python is required', result.stderr)
                    self.assertFalse(output.exists())

    def test_mismatching_candidate_fails_in_normal_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / (SCRIPT + '.json')
            result = run(SCRIPT, OTHER_PROGRAM, [], output)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertTrue(report['mismatch_count'], 'fixture must mismatch')
            self.assertNotEqual(result.returncode, 0, result.stdout[-300:])

    def test_original_candidate_passes_in_normal_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / (SCRIPT + '.json')
            result = run(SCRIPT, ORIGINAL, [], output)
            self.assertEqual(result.returncode, 0,
                             result.stdout[-300:] + result.stderr[-300:])
            self.assertEqual(
                json.loads(output.read_text(encoding='utf-8'))['mismatch_count'],
                0)


if __name__ == '__main__':
    unittest.main()
