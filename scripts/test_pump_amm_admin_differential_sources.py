#!/usr/bin/env python3
"""Actual AMM admin CLI binds its sources from a checkout under a `target` ancestor."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = 'evidence/original/pump_amm/deployed.so'
COPIED = ('scripts/pump_amm_admin_differential.py', 'scripts/pump_differential_output.py',
          'evidence/upstream/pump_amm.json', ORIGINAL,
          'research/imported-lab/analysis/pump_fun/config-snapshot.json')


class AmmAdminSourceBindingTests(unittest.TestCase):
    def test_checkout_under_target_ancestor_binds_only_generated_free_sources(self):
        with tempfile.TemporaryDirectory(prefix='amm-admin-sources-') as temporary:
            checkout = Path(temporary).resolve() / 'target' / 'checkout'
            for name in COPIED:
                (checkout / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, checkout / name)
            source = checkout / 'programs/pump-amm'
            (source / 'src').mkdir(parents=True)
            (source / 'target').mkdir()
            (source / 'src/lib.rs').write_text('// admitted input\n', encoding='utf-8')
            # The crate's own target/ directory is generated output, not a source input.
            (source / 'target/generated.rs').write_text('// generated\n', encoding='utf-8')
            output = Path(temporary) / 'admin.json'
            env = dict(os.environ)
            env.pop('PYTHONOPTIMIZE', None)
            result = subprocess.run([sys.executable, '-B', str(checkout / 'scripts/pump_amm_admin_differential.py'),
                                     '--candidate', str(checkout / ORIGINAL), '--output', str(output), '--quick'],
                                    cwd=checkout, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(output.read_bytes())
            self.assertEqual(report['case_count'], 267)
            self.assertEqual(report['source_sha256'], {
                'programs/pump-amm/src/lib.rs': hashlib.sha256((source / 'src/lib.rs').read_bytes()).hexdigest()})


if __name__ == '__main__':
    unittest.main()
