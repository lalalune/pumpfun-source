"""Mayhem runtime receipts must name the candidate bytes that were executed."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAYHEM = ROOT / 'evidence/original/mayhem/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'
SUITES = ('mayhem_validate_admin', 'mayhem_validate_extend', 'mayhem_validate_fee_recipient',
          'mayhem_validate_withdraw', 'mayhem_validate_sweeps', 'mayhem_validate_quote_withdraw')
# Run the real CLI; mutate the candidate path once, at the first case, after both
# fixtures have loaded their programs. VM execution is not mocked.
DRIVER = '''
import os, runpy, shutil, sys
script, candidate, replacement, output, mode, marker = sys.argv[1:7]
sys.path.insert(0, os.path.dirname(script))
def hook(frame, event, arg):
    if event == 'call' and frame.f_code.co_name == 'execute' and frame.f_code.co_filename == script:
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


class MayhemRuntimeImageBindingTests(unittest.TestCase):
    def run_suite(self, suite, mode):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            candidate, output, marker = temporary / 'candidate.so', temporary / 'report.json', temporary / 'mutated'
            shutil.copyfile(MAYHEM, candidate)
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts' / (suite + '.py')),
                 str(candidate), str(OTHER), str(output), mode, str(marker)],
                cwd=ROOT, capture_output=True, text=True, timeout=300)
            # The hook must have reached the first case after both fixtures loaded.
            self.assertTrue(marker.exists(), suite + ' never reached a case')
            report = json.loads(output.read_text()) if output.is_file() else None
            return result, report

    def test_receipt_binds_the_executed_candidate(self):
        executed = sha(MAYHEM)
        self.assertNotEqual(executed, sha(OTHER))
        for suite in SUITES:
            control, control_report = self.run_suite(suite, 'none')
            self.assertEqual(control.returncode, 0, control.stderr)
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
