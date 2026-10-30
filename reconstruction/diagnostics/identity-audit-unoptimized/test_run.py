"""Actual optimized CLI regressions over a retained Associated Token ELF."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
            # The retained audit now refuses to replace a published report, so an
            # optimized rerun preserves the earlier bytes instead of erasing them.
            # Previously this case asserted the opposite: that optimized Python let
            # the legacy run overwrite its own report.
            for name, script in [('legacy', legacy), ('entrypoint', PACKAGE / 'run.py')]:
                with self.subTest(runner=name):
                    repeat = invoke(script, 'index-b.json', output, optimized=True)
                    self.assertNotEqual(repeat.returncode, 0)
                    self.assertEqual(output.read_bytes(), prior)
            for field in ['original_sha256', 'candidate_sha256']:
                wrong = {**row, field: '0' * 64}
                (root / 'wrong.json').write_text(json.dumps({'programs': {'wrong-control': wrong}}), encoding='utf-8')
                # The legacy run rejects a wrong digest under -O as well; both
                # runners must fail without publishing a report.
                for name, script in [('legacy', legacy), ('entrypoint', PACKAGE / 'run.py')]:
                    with self.subTest(field=field, runner=name):
                        target = root / f'rejected-{name}-{field}.json'
                        denied = invoke(script, 'wrong.json', target, optimized=True,
                                        env=dict(os.environ, PYTHONOPTIMIZE='2'))
                        self.assertNotEqual(denied.returncode, 0)
                        self.assertIn(f"{field.split('_')[0]} SHA-256 mismatch", denied.stderr)
                        self.assertFalse(target.exists())
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


class ReviewedSourceControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='identity-reviewed-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sources = {}
        for name in ('reconstruction_identity_audit.py', 'analyze.py', 'compare.py'):
            path = self.root / 'scripts' / name
            path.parent.mkdir(exist_ok=True)
            self.sources[path] = (ROOT / 'scripts' / name).read_bytes()
            path.write_bytes(self.sources[path])
        raw = (ROOT / 'evidence/dependencies/associated_token/deployed.so').read_bytes()
        (self.root / 'original.so').write_bytes(raw)
        (self.root / 'candidate.so').write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        (self.root / 'index.json').write_text(json.dumps({'programs': {'control': {
            'original_path': 'original.so', 'candidate_path': 'candidate.so',
            'original_sha256': sha, 'candidate_sha256': sha}}}))
        spec = importlib.util.spec_from_file_location('identity_entrypoint', PACKAGE / 'run.py')
        self.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runner)

    def test_each_modified_reviewed_source_is_rejected(self):
        for index, (path, raw) in enumerate(self.sources.items()):
            with self.subTest(source=path.name):
                path.write_bytes(raw + b'\n# source mutation\n')
                output = self.root / f'rejected-{index}.json'
                result = subprocess.run([sys.executable, '-O', '-B', str(PACKAGE / 'run.py'),
                    '--repo', str(self.root), '--index', 'index.json', '--output', str(output)],
                    capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('reviewed identity audit source changed', result.stderr)
                self.assertFalse(output.exists())
                path.write_bytes(raw)

    def test_child_uses_admitted_sources_after_public_paths_change(self):
        for index, (path, raw) in enumerate(self.sources.items()):
            with self.subTest(source=path.name):
                output = self.root / f'bound-{index}.json'
                def mutate_then_run(command):
                    path.write_text("raise RuntimeError('unreviewed source executed')\n")
                    result = subprocess.run(command, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    return result.returncode
                try:
                    with mock.patch.object(sys, 'argv', [str(PACKAGE/'run.py'), '--repo', str(self.root),
                         '--index', 'index.json', '--output', str(output)]), \
                         mock.patch.object(self.runner.subprocess, 'call', mutate_then_run):
                        self.assertEqual(self.runner.main(), 0)
                    self.assertNotEqual(path.read_bytes(), raw)
                    report = json.loads(output.read_text())
                    self.assertTrue(report['snapshot_programs']['control']['allocation_comparison']['full_byte_equality'])
                    self.assertFalse(report['current_status_file']['exists'])
                finally:
                    path.write_bytes(raw)

    def test_late_report_is_preserved_by_child(self):
        output = self.root / 'late.json'
        def publish_then_run(command):
            output.write_bytes(b'late writer receipt')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Preserve prior audits', result.stderr)
            return result.returncode
        with mock.patch.object(sys, 'argv', [str(PACKAGE/'run.py'), '--repo', str(self.root),
             '--index', 'index.json', '--output', str(output)]), \
             mock.patch.object(self.runner.subprocess, 'call', publish_then_run):
            self.assertNotEqual(self.runner.main(), 0)
        self.assertEqual(output.read_bytes(), b'late writer receipt')


if __name__ == '__main__':
    unittest.main()
