"""Actual optimized CLI regressions over a retained Associated Token ELF."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent


class UnoptimizedIdentityTests(unittest.TestCase):
    def test_optimized_invocations_cannot_erase_bindings_or_overwrite_reports(self):
        with tempfile.TemporaryDirectory(prefix='pump-identity-opt-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-identity-opt-'))
            for name in ['reconstruction_identity_audit.py', 'analyze.py', 'compare.py']:
                target = root / 'scripts' / name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(ROOT / 'scripts' / name, target)
            (root / 'repro').mkdir()
            (root / 'repro/status.json').write_text('{}', encoding='utf-8')
            raw = (ROOT / 'evidence/dependencies/associated_token/deployed.so').read_bytes()
            (root / 'original.so').write_bytes(raw)
            (root / 'candidate-control.so').write_bytes(raw)
            sha = hashlib.sha256(raw).hexdigest()
            row = {'original_path': 'original.so', 'candidate_path': 'candidate-control.so',
                   'original_sha256': sha, 'candidate_sha256': sha}
            for name, label in [('index-a.json', 'first-control'), ('index-b.json', 'second-control')]:
                (root / name).write_text(json.dumps({'programs': {label: row}}), encoding='utf-8')
            def invoke(script, index, output, optimized=False, env=None):
                return subprocess.run([sys.executable, *(['-O'] if optimized else []), '-B', '-X', 'utf8',
                                       str(script), '--repo', str(root), '--index', index, '--output', str(output)],
                                      cwd=root, env=env, capture_output=True, text=True, encoding='utf-8')
            legacy = root / 'scripts/reconstruction_identity_audit.py'
            output = root / 'prior-report.json'
            initial = invoke(legacy, 'index-a.json', output)
            self.assertEqual(initial.returncode, 0, initial.stdout + initial.stderr)
            prior = output.read_bytes()
            overwrite = invoke(legacy, 'index-b.json', output, optimized=True)
            self.assertEqual(overwrite.returncode, 0, overwrite.stdout + overwrite.stderr)
            self.assertNotEqual(output.read_bytes(), prior)
            output.write_bytes(prior)
            guarded = invoke(PACKAGE / 'run.py', 'index-b.json', output, optimized=True)
            self.assertNotEqual(guarded.returncode, 0)
            self.assertEqual(output.read_bytes(), prior)
            for field in ['original_sha256', 'candidate_sha256']:
                wrong = {**row, field: '0' * 64}
                (root / 'wrong.json').write_text(json.dumps({'programs': {'wrong-control': wrong}}), encoding='utf-8')
                accepted = invoke(legacy, 'wrong.json', root / f'old-{field}.json', optimized=True)
                self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
                denied = invoke(PACKAGE / 'run.py', 'wrong.json', root / f'fixed-{field}.json', optimized=True,
                                env=dict(os.environ, PYTHONOPTIMIZE='2'))
                self.assertNotEqual(denied.returncode, 0)
                self.assertFalse((root / f'fixed-{field}.json').exists())
            fresh = root / 'fresh.json'
            valid = invoke(PACKAGE / 'run.py', 'index-a.json', fresh, optimized=True,
                           env=dict(os.environ, PYTHONOPTIMIZE='2'))
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
            report = json.loads(fresh.read_text(encoding='utf-8'))
            control = report['snapshot_programs']['first-control']
            self.assertTrue(control['allocation_comparison']['full_byte_equality'])
            self.assertFalse(control['source_completeness_inferred'])
            self.assertFalse(control['historical_compiler_identity_proven'])
            self.assertEqual(report['input_sha256']['candidate-control.so'], sha)
            self.assertEqual((root / 'candidate-control.so').read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
