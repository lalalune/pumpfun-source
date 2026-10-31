"""Report writers bind the trade-fixture files they read at import."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_trade_fixture import REPORT_INPUTS

SCRIPTS = ('pump_validate_constant_product.py', 'pump_validate_sell_accounting.py')
HOST = ROOT / 'evidence/original/pump/deployed.so'
INPUTS = (
    ROOT / 'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
    ROOT / 'evidence/original/pump/capture.json',
    ROOT / 'scripts/pump_trade_fixture.py',
)


class FixtureInputBindingTests(unittest.TestCase):
    def test_fixture_inputs_cannot_be_report_outputs(self):
        self.assertLessEqual(set(INPUTS), set(REPORT_INPUTS))
        for script in SCRIPTS:
            for path in INPUTS:
                with self.subTest(script=script, path=str(path.relative_to(ROOT))):
                    before = path.read_bytes()
                    result = subprocess.run(
                        [sys.executable, '-B', str(ROOT / 'scripts' / script),
                         '--host', str(HOST), '--output', str(path)],
                        cwd=ROOT, capture_output=True, text=True, timeout=300)
                    self.assertNotEqual(result.returncode, 0, result.stdout[-2000:])
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
