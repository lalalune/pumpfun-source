#!/usr/bin/env python3
"""The quote-control report binds fallback sources in a checkout under a `target` ancestor."""
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
COPIED = ('scripts/pump_quote_control_fresh_differential.py', 'scripts/pump_diagnostic_audit.py',
          'scripts/pump_differential_output.py', 'evidence/upstream/pump.json', ORIGINAL,
          'research/imported-lab/analysis/pump_fun/config-snapshot.json')
# The fallback binding runs before any case; no VM execution is needed to reach it.
DRIVER = r'''
import sys
checkout, candidate, output = sys.argv[1:]
sys.path.insert(0, checkout + '/scripts')
import pump_quote_control_fresh_differential as tool
tool.cases = lambda: []
sys.argv = [tool.__file__, '--candidate', candidate, '--output', output]
tool.main()
'''


class FallbackSourceBindingTests(unittest.TestCase):
    def test_checkout_under_target_ancestor_binds_only_generated_free_sources(self):
        with tempfile.TemporaryDirectory(prefix='quote-control-sources-') as temporary:
            temporary = Path(temporary).resolve()
            checkout = temporary / 'target' / 'checkout'
            for name in COPIED:
                (checkout / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, checkout / name)
            source = checkout / 'programs/pump'
            (source / 'src').mkdir(parents=True)
            (source / 'target').mkdir()
            (source / 'Cargo.toml').write_text('[package]\n', encoding='utf-8')
            (source / 'src/lib.rs').write_text('// admitted input\n', encoding='utf-8')
            # The crate's own target/ directory is generated output, not a source input.
            (source / 'target/generated.rs').write_text('// generated\n', encoding='utf-8')
            # No adjacent build-comparison.json: the independently supplied ELF path.
            supplied = temporary / 'supplied'
            supplied.mkdir()
            candidate = supplied / 'candidate.so'
            shutil.copyfile(ROOT / ORIGINAL, candidate)
            output = temporary / 'report.json.gz'
            env = dict(os.environ)
            env.pop('PYTHONOPTIMIZE', None)
            result = subprocess.run([sys.executable, '-B', '-c', DRIVER, str(checkout), str(candidate), str(output)],
                                    cwd=checkout, env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            bound = json.loads(gzip.decompress(output.read_bytes()))['bound_inputs_sha256']
            sources = {name: value for name, value in bound.items() if name.startswith('programs/')}
            self.assertEqual(sources, {
                'programs/pump/Cargo.toml': hashlib.sha256((source / 'Cargo.toml').read_bytes()).hexdigest(),
                'programs/pump/src/lib.rs': hashlib.sha256((source / 'src/lib.rs').read_bytes()).hexdigest()})


if __name__ == '__main__':
    unittest.main()
