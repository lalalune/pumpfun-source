"""Execute full Fees suites while replacing the candidate path after VM loading."""
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/original/pump_fees/deployed.so'
REPLACEMENT = ROOT / 'evidence/original/mayhem/deployed.so'
SUITES = ('fees_admin_differential.py', 'fees_config_differential.py',
          'fees_extend_differential.py', 'fees_deprecated_differential.py',
          'fees_upsert_differential.py', 'fees_admin_transfer_differential.py',
          'fees_initialize_differential.py')


def run_instrumented_suite(script_name, candidate, output, mutation, marker):
    """Schedule a real file mutation after both real fixture constructors finish."""
    if script_name not in SUITES:
        raise ValueError('unknown suite')
    script = ROOT / 'scripts' / script_name
    mutated = False

    def local_trace(frame, event, argument):
        nonlocal mutated
        if event == 'line' and frame.f_locals.get('b') is not None:
            if mutation == 'replace':
                candidate.write_bytes(REPLACEMENT.read_bytes())
            elif mutation == 'delete':
                candidate.unlink()
            else:
                raise ValueError('unknown mutation')
            marker.write_text(mutation, encoding='utf-8')
            mutated = True
            sys.settrace(None)
        return local_trace

    def global_trace(frame, event, argument):
        if frame.f_code.co_filename == str(script) and frame.f_code.co_name == 'main':
            return local_trace
        return None

    sys.path.insert(0, str(ROOT / 'scripts'))
    sys.argv = [str(script), '--candidate', str(candidate), '--output', str(output)]
    if mutation != 'control':
        sys.settrace(global_trace)
    try:
        runpy.run_path(str(script), run_name='__main__')
    finally:
        sys.settrace(None)
    if mutation != 'control' and not mutated:
        raise RuntimeError('post-load mutation was never reached')


class FeesRuntimeImageBindingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='fees-runtime-image-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.expected = hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()

    def run_suite(self, script, mutation):
        candidate = self.work / 'candidate.so'
        output = self.work / 'report.json'
        marker = self.work / 'mutated'
        shutil.copyfile(ORIGINAL, candidate)
        output.unlink(missing_ok=True)
        marker.unlink(missing_ok=True)
        result = subprocess.run(
            [sys.executable, '-B', str(Path(__file__).resolve()), '--run-suite',
             script, str(candidate), str(output), mutation, str(marker)],
            cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout[-1000:] + result.stderr)
        if mutation != 'control':
            self.assertEqual(marker.read_text(encoding='utf-8'), mutation)
            if mutation == 'replace':
                self.assertEqual(candidate.read_bytes(), REPLACEMENT.read_bytes())
            else:
                self.assertFalse(candidate.exists())
        return json.loads(output.read_bytes())

    def test_full_suite_receipts_keep_the_hash_of_the_executed_image(self):
        for script in SUITES:
            with self.subTest(script=script, mutation='control'):
                control = self.run_suite(script, 'control')
                self.assertEqual(control['candidate_sha256'], self.expected)
                self.assertEqual(control['original_sha256'], self.expected)
                self.assertEqual(control['mismatches'], [])
                self.assertGreater(control['case_count'], 0)
            for mutation in ('replace', 'delete'):
                with self.subTest(script=script, mutation=mutation):
                    observed = self.run_suite(script, mutation)
                    self.assertEqual(observed['candidate_sha256'], self.expected)
                    self.assertEqual(observed, control)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--run-suite':
        name, candidate, output, mutation, marker = sys.argv[2:]
        run_instrumented_suite(name, Path(candidate), Path(output), mutation, Path(marker))
    else:
        unittest.main()
