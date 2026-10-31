"""Real AMM CLIs must preserve the caller-relative fixtures they actually read."""
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TRADE = 'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'
MIGRATION = 'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'
IDL = 'evidence/upstream/pump.json'


class AmmCallerFixtureInputsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='amm-caller-inputs-')
        self.addCleanup(self.temporary.cleanup)
        self.caller = Path(self.temporary.name)
        self.inputs = {}
        for name in (TRADE, MIGRATION, IDL):
            target = self.caller / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
            self.inputs[target] = target.read_bytes()

    def invoke(self, script, output):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts' / script),
                               '--candidate', str(ROOT / 'evidence/original/pump_amm/deployed.so'),
                               '--output', str(output)], cwd=self.caller, env=env,
                              capture_output=True, text=True, timeout=240)

    def unchanged(self):
        for path, raw in self.inputs.items():
            self.assertEqual(path.read_bytes(), raw, str(path))

    def test_actual_caller_fixture_outputs_are_refused(self):
        scripts = {
            'pump_amm_collect_differential.py': (TRADE,),
            'pump_amm_migration_create_differential.py': (TRADE, MIGRATION, IDL),
            'pump_amm_transfer_creator_differential.py': (TRADE, IDL),
            'pump_amm_boost_differential.py': (TRADE, MIGRATION, IDL),
        }
        for script, inputs in scripts.items():
            for name in inputs:
                with self.subTest(script=script, fixture=name):
                    result = self.invoke(script, self.caller / name)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('report output aliases an input', result.stderr)
                    self.unchanged()

    def test_inherited_trade_fixture_link_aliases_are_refused(self):
        for kind in ('symlink', 'hardlink'):
            with self.subTest(kind=kind):
                output = self.caller / (kind + '.json')
                try:
                    if kind == 'symlink':
                        output.symlink_to(self.caller / TRADE)
                    else:
                        os.link(self.caller / TRADE, output)
                except OSError as error:
                    if error.errno in (errno.EACCES, errno.EPERM, errno.ENOSYS, errno.ENOTSUP):
                        self.skipTest(f'{kind} unavailable on this platform: {error}')
                    raise
                result = self.invoke('pump_amm_collect_differential.py', output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('report output aliases an input', result.stderr)
                self.unchanged()

    def test_independent_output_runs_real_captured_corpus(self):
        output = self.caller / 'reports' / 'collect.json'
        result = self.invoke('pump_amm_collect_differential.py', output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(output.read_bytes())
        self.assertEqual(report['case_count'], 148)
        self.assertEqual(report['mismatches'], [])
        self.unchanged()


if __name__ == '__main__':
    unittest.main()
