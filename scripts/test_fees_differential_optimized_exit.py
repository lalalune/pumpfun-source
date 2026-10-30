#!/usr/bin/env python3
"""Fees differentials must fail on mismatches in every optimization mode.

These seven suites gated their exit status on `assert not failures`. `python -O`
and PYTHONOPTIMIZE strip asserts, so a candidate that mismatched every case
still exited 0. The candidate here is a real program that is not Pump Fees: the
captured Mayhem deployment loaded at the Fees address. Every case mismatches.
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
SUITES = [
    'fees_admin_differential.py',
    'fees_admin_transfer_differential.py',
    'fees_config_differential.py',
    'fees_deprecated_differential.py',
    'fees_extend_differential.py',
    'fees_initialize_differential.py',
    'fees_upsert_differential.py',
]
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
OTHER_PROGRAM = ROOT / 'evidence/original/mayhem/deployed.so'


def run(script, candidate, flags, output):
    env = dict(os.environ)
    env.pop('PYTHONOPTIMIZE', None)
    return subprocess.run(
        [sys.executable, *flags, '-B', str(ROOT / 'scripts' / script),
         '--candidate', str(candidate), '--output', str(output)],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')


class OptimizedExitTests(unittest.TestCase):
    def test_mismatching_candidate_fails_in_every_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            for script in SUITES:
                for flags in ([], ['-O'], ['-OO']):
                    with self.subTest(script=script, flags=flags):
                        output = Path(temp) / (script + ''.join(flags) + '.json')
                        result = run(script, OTHER_PROGRAM, flags, output)
                        report = json.loads(output.read_text(encoding='utf-8'))
                        self.assertTrue(report['mismatches'], 'fixture must mismatch')
                        self.assertNotEqual(result.returncode, 0, result.stdout[-300:])

    def test_original_candidate_still_passes_optimized(self):
        with tempfile.TemporaryDirectory() as temp:
            for script in SUITES:
                with self.subTest(script=script):
                    output = Path(temp) / (script + '.json')
                    result = run(script, ORIGINAL, ['-O'], output)
                    self.assertEqual(result.returncode, 0, result.stdout[-300:] + result.stderr[-300:])
                    self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['mismatches'], [])


if __name__ == '__main__':
    unittest.main()
