"""The v3 report writers publish through the input-preserving publisher."""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ('pump_v3_configured_fee_differential.py', 'pump_v3_token_extensions_differential.py')
INPUTS = ('research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
          'evidence/original/pump/capture.json')


class V3WriterPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='v3-output-binding-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'scripts').mkdir()
        for path in (ROOT / 'scripts').glob('*.py'):
            shutil.copyfile(path, self.root / 'scripts' / path.name)
        data = [INPUTS[0]]
        data += [f'evidence/{group}/{name}/{filename}'
                 for group, names in [('original', ('pump', 'pump_fees')),
                                      ('dependencies', ('spl_token', 'spl_token_2022', 'associated_token'))]
                 for name in names for filename in ('capture.json', 'deployed.so')]
        for name in data:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def run_script(self, script, output):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        return subprocess.run(
            [sys.executable, '-B', str(self.root / 'scripts' / script),
             '--candidate', str(self.root / 'evidence/original/pump/deployed.so'), '--output', str(output)],
            cwd=self.root, env=env, capture_output=True, text=True, timeout=600)

    def test_fixture_inputs_cannot_be_report_outputs(self):
        for script in SCRIPTS:
            for name in INPUTS:
                path = self.root / name
                with self.subTest(script=script, path=path.name):
                    before = path.read_bytes()
                    result = self.run_script(script, path)
                    self.assertNotEqual(result.returncode, 0, result.stdout[-2000:])
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(path.read_bytes(), before)

    def test_reports_still_publish_to_a_fresh_output(self):
        expected = dict(zip(SCRIPTS, (372, 126)))
        for script in SCRIPTS:
            payloads = []
            for suffix in ('.json', '.json.gz'):
                with self.subTest(script=script, suffix=suffix):
                    output = self.root / (script + suffix)
                    result = self.run_script(script, output)
                    self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                    wire = output.read_bytes()
                    raw = gzip.decompress(wire) if suffix.endswith('.gz') else wire
                    if suffix.endswith('.gz'):
                        self.assertEqual(wire[4:8], b'\0' * 4)
                    payloads.append(raw)
                    report = json.loads(raw)
                    self.assertEqual(report['case_count'], expected[script])
                    self.assertEqual(len(report['cases']), expected[script])
                    self.assertEqual(report['mismatches'], [])
                    self.assertEqual(report['candidate_sha256'], hashlib.sha256(
                        (self.root / 'evidence/original/pump/deployed.so').read_bytes()).hexdigest())
            self.assertEqual(payloads[0], payloads[1])


if __name__ == '__main__':
    unittest.main()
