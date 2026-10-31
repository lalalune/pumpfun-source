"""Real LiteSVM cases keep the default oracle and its reported digest together."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fees_sharing_create_differential as sharing

FIELDS = ('error', 'sharing', 'curve', 'payer_lamports', 'authority_lamports',
          'sharing_lamports', 'pool', 'pool_lamports', 'curve_lamports', 'events', 'inner')


class SharingOracleBindingTests(unittest.TestCase):
    def run_cases(self, root, replace):
        for name in ('pump', 'pump_amm', 'pump_fees'):
            target = root / f'evidence/original/{name}/deployed.so'
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / f'evidence/original/{name}/deployed.so', target)
        original = root / 'evidence/original/pump_fees/deployed.so'
        admitted = hashlib.sha256(original.read_bytes()).hexdigest()
        replacement = ROOT / 'evidence/original/mayhem/deployed.so'
        cases = sharing.cases()[:3]
        output = root / 'report.json'
        changed = False

        def trace(frame, event, value):
            nonlocal changed
            if (replace and not changed and event == 'return'
                    and frame.f_code is sharing.run.__code__):
                staged = original.with_suffix('.new')
                shutil.copyfile(replacement, staged)
                staged.replace(original)
                changed = True
            return trace

        previous = sys.gettrace()
        try:
            if replace:
                sys.settrace(trace)
            with patch.object(sharing, 'ROOT', root), patch.object(sharing, 'cases', return_value=cases), \
                    patch.object(sys, 'argv', ['sharing', '--output', str(output)]), \
                    contextlib.redirect_stdout(io.StringIO()):
                sharing.main()
        finally:
            sys.settrace(previous)
        if replace:
            self.assertTrue(changed)
            self.assertEqual(original.read_bytes(), replacement.read_bytes())
        report = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual(report['original_sha256'], admitted)
        self.assertEqual(len(report['cases']), 3)
        return report

    def test_replacing_default_oracle_after_case_one_keeps_the_admitted_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stable = self.run_cases(root / 'stable', False)
            replaced = self.run_cases(root / 'replaced', True)
        self.assertIsNone(stable['cases'][0]['original']['error'])
        for left, right in zip(stable['cases'], replaced['cases']):
            self.assertEqual(left['case'], right['case'])
            for field in FIELDS:
                self.assertEqual(left['original'][field], right['original'][field], field)


if __name__ == '__main__':
    unittest.main()
