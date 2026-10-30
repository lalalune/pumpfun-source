#!/usr/bin/env python3
"""The serial Fees aggregate must bound each suite with a killable process group."""
from pathlib import Path
import subprocess
import sys
import time

import test_fees_aggregate_output as fixtures
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/fees_validate_all.py'
CANDIDATE = ROOT / 'evidence/original/pump_fees/deployed.so'


class FeesSuiteTimeoutTests(unittest.TestCase):
    def invoke(self, output, timeout):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(CANDIDATE),
             '--output', str(output), '--suite-timeout', timeout],
            capture_output=True, text=True, timeout=120)

    def test_expired_suite_is_killed_and_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.json.gz'
            result = self.invoke(output, '0.001')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stderr.strip().splitlines()[-1], 'suite queries exceeded 0.001s')
            self.assertFalse(output.exists())

    def test_nonpositive_timeout_is_rejected(self):
        for timeout in ('0', '-1', 'nan', 'inf'):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'report.json.gz'
                result = self.invoke(output, timeout)
                self.assertEqual(result.returncode, 1)
                self.assertIn('compiler timeout must be a positive finite number of seconds',
                              result.stderr)
                self.assertFalse(output.exists())


    @unittest.skipUnless(sys.platform != 'win32', 'POSIX process-group guarantee')
    def test_actual_aggregate_timeout_kills_descendant_and_preserves_prior_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = fixtures.FeesAggregateOutputTests().fixture(root)
            marker = root / 'survivor'
            child = ('import subprocess,sys,time;print("suite started",flush=True);'
                     'subprocess.Popen([sys.executable,"-c",'
                     f'"import time,pathlib;time.sleep(0.8);pathlib.Path({str(marker)!r}).write_text(\'survived\')"]);'
                     'time.sleep(30)')
            (root / 'scripts/validate_fee_handlers.py').write_text(child)
            output = root / 'prior.json'
            output.write_bytes(b'prior report')
            result = subprocess.run([sys.executable, '-B', str(root / 'scripts/fees_validate_all.py'),
                '--candidate', str(candidate), '--output', str(output), '--suite-timeout', '0.3'],
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('suite queries exceeded 0.3s', result.stderr)
            self.assertIn('suite started', result.stdout)
            self.assertEqual(output.read_bytes(), b'prior report')
            time.sleep(1)
            self.assertFalse(marker.exists())

    def test_process_helper_output_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = fixtures.FeesAggregateOutputTests().fixture(root)
            output = root / 'reconstruction/harness/build_process.py'
            before = output.read_bytes()
            result = subprocess.run([sys.executable, '-B', str(root/'scripts/fees_validate_all.py'),
                '--candidate',str(candidate),'--output',str(output)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('report output aliases an input', result.stderr)
            self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
