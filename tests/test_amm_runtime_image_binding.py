"""PumpSwap administration receipts must name the candidate bytes that were executed."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
AMM = ROOT / 'evidence/original/pump_amm/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'
SUITES = ('pump_amm_admin_differential', 'pump_amm_accumulator_differential', 'pump_amm_buyback_differential',
          'pump_amm_fee_config_differential', 'pump_amm_resize_differential', 'pump_amm_reserved_differential')
# Run the real CLI. Every suite builds the original harness, then the candidate harness,
# through pump_amm_admin_differential.Harness.__init__; mutate the candidate path once,
# after the second construction returns. VM execution is not mocked.
DRIVER = '''
import os, runpy, shutil, sys
script, harness, candidate, replacement, output, mode, marker = sys.argv[1:8]
sys.path.insert(0, os.path.dirname(script))
built = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == '__init__' and frame.f_code.co_filename == harness:
        built.append(1)
        if len(built) == 2:
            sys.setprofile(None)
            open(marker, 'w').close()
            if mode == 'replace':
                shutil.copyfile(replacement, candidate)
            elif mode == 'delete':
                os.remove(candidate)
sys.argv = [script, '--candidate', candidate, '--output', output]
sys.setprofile(hook)
runpy.run_path(script, run_name='__main__')
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AmmRuntimeImageBindingTests(unittest.TestCase):
    def run_suite(self, suite, mode):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            candidate, output, marker = temporary / 'candidate.so', temporary / 'report.json', temporary / 'mutated'
            shutil.copyfile(AMM, candidate)
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts' / (suite + '.py')),
                 str(ROOT / 'scripts/pump_amm_admin_differential.py'),
                 str(candidate), str(OTHER), str(output), mode, str(marker)],
                cwd=ROOT, capture_output=True, text=True, timeout=600)
            # Both harnesses must have been built before the mutation.
            self.assertTrue(marker.exists(), suite + ' never built both harnesses')
            report = json.loads(output.read_text()) if output.is_file() else None
            return result, report

    def test_receipt_binds_the_executed_candidate(self):
        executed = sha(AMM)
        self.assertNotEqual(executed, sha(OTHER))
        for suite in SUITES:
            control, control_report = self.run_suite(suite, 'none')
            self.assertEqual(control.returncode, 0, control.stderr[-2000:])
            self.assertEqual(control_report['original_sha256'], executed)
            self.assertEqual(control_report['candidate_sha256'], executed)
            self.assertEqual(control_report['mismatches'], [])
            self.assertGreater(control_report['case_count'], 0)
            for mode in ('replace', 'delete'):
                with self.subTest(suite=suite, mode=mode):
                    result, report = self.run_suite(suite, mode)
                    self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                    self.assertEqual(report, control_report)


if __name__ == '__main__':
    unittest.main()
