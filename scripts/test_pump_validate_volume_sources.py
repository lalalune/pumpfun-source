#!/usr/bin/env python3
"""Actual volume-suite CLI binds its sources from a checkout under a `target` ancestor."""
import gzip
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
ORIGINAL = 'evidence/original/pump/deployed.so'
COPIED = ('scripts/pump_validate_volume.py', 'scripts/pump_differential_output.py',
          'scripts/pump_amm_reusable_harness.py', 'evidence/upstream/pump.json', ORIGINAL)


class VolumeSourceBindingTests(unittest.TestCase):
    def test_checkout_under_target_ancestor_binds_only_generated_free_sources(self):
        with tempfile.TemporaryDirectory(prefix='volume-sources-') as temporary:
            checkout = Path(temporary) / 'target' / 'checkout'
            for name in COPIED:
                (checkout / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, checkout / name)
            source = checkout / 'programs/pump'
            (source / 'src').mkdir(parents=True)
            (source / 'target').mkdir()
            (source / 'Cargo.toml').write_text('[package]\nname = "fixture"\n', encoding='utf-8')
            (source / 'src/lib.rs').write_text('// admitted input\n', encoding='utf-8')
            # The crate's own target/ directory is generated output, not a source input.
            (source / 'target/generated.rs').write_text('// generated\n', encoding='utf-8')
            output = Path(temporary) / 'volume.json.gz'
            env = dict(os.environ)
            env.pop('PYTHONOPTIMIZE', None)
            result = subprocess.run([sys.executable, '-B', str(checkout / 'scripts/pump_validate_volume.py'),
                                     '--candidate', str(checkout / ORIGINAL), '--output', str(output)],
                                    cwd=checkout, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(gzip.decompress(output.read_bytes()))
            self.assertEqual(report['case_count'], 66)
            self.assertEqual(report['source_sha256'], {
                name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                for name in ('Cargo.toml', str(Path('src/lib.rs')))})


if __name__ == '__main__':
    unittest.main()
