"""The v3 report writers publish through the input-preserving publisher."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ('pump_v3_configured_fee_differential.py', 'pump_v3_token_extensions_differential.py')
INPUTS = (
    ROOT / 'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
    ROOT / 'evidence/original/pump/capture.json',
)


class V3WriterPublicationTests(unittest.TestCase):
    def run_script(self, script, output):
        return subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts' / script), '--output', str(output)],
            cwd=ROOT, capture_output=True, text=True, timeout=600)

    def test_fixture_inputs_cannot_be_report_outputs(self):
        for script in SCRIPTS:
            for path in INPUTS:
                with self.subTest(script=script, path=path.name):
                    before = path.read_bytes()
                    result = self.run_script(script, path)
                    self.assertNotEqual(result.returncode, 0, result.stdout[-2000:])
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(path.read_bytes(), before)

    def test_reports_still_publish_to_a_fresh_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            for script in SCRIPTS:
                with self.subTest(script=script):
                    output = Path(temporary) / (script + '.json')
                    result = self.run_script(script, output)
                    self.assertEqual(result.returncode, 0, result.stderr[-2000:])
                    report = json.loads(output.read_text())
                    self.assertGreater(report['case_count'], 0)
                    self.assertEqual(report['mismatches'], [])


if __name__ == '__main__':
    unittest.main()
