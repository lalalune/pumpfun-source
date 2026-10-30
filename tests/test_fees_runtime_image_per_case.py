"""Fees suites that build a VM per case must execute and report one candidate image per run."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FEES = ROOT / 'evidence/original/pump_fees/deployed.so'
OTHER = ROOT / 'evidence/original/pump_amm/deployed.so'
# The two cheapest of the four changed suites; buyback and social_claim_v2 take the same
# one-line change and were checked by full-report comparison instead.
SUITES = ('fees_social_create_differential', 'fees_withdraw_differential')
# Run the real CLI. Each case runs the original, then the candidate, in a fresh VM;
# mutate the candidate path once the first candidate run returns, so later cases
# would load the new bytes. VM execution is not mocked.
DRIVER = '''
import os, runpy, shutil, sys
script, candidate, replacement, output, mode, marker = sys.argv[1:7]
sys.path.insert(0, os.path.dirname(script))
runs = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'run' and frame.f_code.co_filename == script:
        runs.append(1)
        if len(runs) == 2:
            sys.setprofile(None)
            open(marker, 'w').close()
            if mode == 'replace':
                shutil.copyfile(replacement, candidate)
            elif mode == 'delete':
                os.remove(candidate)
            elif mode == 'retarget':
                os.symlink(replacement, candidate + '.next')
                os.replace(candidate + '.next', candidate)
sys.argv = [script, '--candidate', candidate, '--output', output]
sys.setprofile(hook)
runpy.run_path(script, run_name='__main__')
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FeesRuntimeImagePerCaseTests(unittest.TestCase):
    def run_suite(self, suite, mode):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            candidate, output, marker = temporary / 'candidate.so', temporary / 'report.json', temporary / 'mutated'
            if mode == 'retarget':
                # A symlinked candidate whose link is pointed at other bytes mid-run.
                shutil.copyfile(FEES, temporary / 'built.so')
                candidate.symlink_to(temporary / 'built.so')
            else:
                shutil.copyfile(FEES, candidate)
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts' / (suite + '.py')),
                 str(candidate), str(OTHER), str(output), mode, str(marker)],
                cwd=ROOT, capture_output=True, text=True, timeout=600)
            # The first case must have run the candidate before the mutation.
            self.assertTrue(marker.exists(), suite + ' never ran a candidate case')
            report = json.loads(output.read_text()) if output.is_file() else None
            return result, report

    def test_run_executes_and_reports_one_candidate_image(self):
        executed = sha(FEES)
        self.assertNotEqual(executed, sha(OTHER))
        for suite in SUITES:
            with self.subTest(suite=suite):
                control, control_report = self.run_suite(suite, 'none')
                self.assertEqual(control.returncode, 0, control.stderr[-2000:])
                self.assertEqual(control_report['original_sha256'], executed)
                self.assertEqual(control_report['candidate_sha256'], executed)
                self.assertEqual(control_report['mismatches'], [])
                self.assertGreater(len(control_report['cases']), 1)
                for mode in ('replace', 'delete', 'retarget'):
                    with self.subTest(suite=suite, mode=mode):
                        result, report = self.run_suite(suite, mode)
                        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                        self.assertEqual(report, control_report)


if __name__ == '__main__':
    unittest.main()
