#!/usr/bin/env python3
"""The Mayhem initialize_mayhem_state differential must fail on candidate divergence.

Its exit status used to depend only on the original reaching the expected
signer gate, so a candidate that diverged on every case still exited 0. The
mismatching candidate here is a real program that is not Mayhem (the captured
Pump deployment loaded at the Mayhem address). The captured Mayhem original is
the control.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/mayhem_initialize_state_differential.py'


def run(candidate, output):
    return subprocess.run([sys.executable, '-B', str(SCRIPT), '--candidate', str(candidate),
                           '--output', str(output)], cwd=ROOT, capture_output=True,
                          text=True, encoding='utf-8')


class InitializeStateExitTests(unittest.TestCase):
    def test_divergent_candidate_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'report.json'
            result = run(ROOT / 'evidence/original/pump/deployed.so', output)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(len(report['mismatches']), report['case_count'])
            self.assertEqual(result.returncode, 1, result.stdout[-300:] + result.stderr[-300:])

    def test_original_candidate_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'report.json'
            result = run(ROOT / 'evidence/original/mayhem/deployed.so', output)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['mismatches'], [])
            self.assertTrue(report['terminal_blocker_confirmed'])
            self.assertEqual(result.returncode, 0, result.stdout[-300:] + result.stderr[-300:])


if __name__ == '__main__':
    unittest.main()
