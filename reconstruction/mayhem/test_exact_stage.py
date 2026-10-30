#!/usr/bin/env python3
"""Real stage-only CLI and sealed-input mutations; no compiler, SDK or network."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from verify_stage import verify

ROOT = Path(__file__).resolve().parents[2]


class ExactStageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mayhem-stage-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / 'public inputs'
        shutil.copytree(ROOT / 'programs/mayhem', self.root / 'programs/mayhem')
        manifest_path = ROOT / 'reconstruction/mayhem/recovered-stage-inputs.json'
        manifest = json.loads(manifest_path.read_text())
        for row in manifest['files'] + [manifest['checkout_policy']]:
            target = self.root / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / row['path'], target)
        target = self.root / 'reconstruction/mayhem/recovered-stage-inputs.json'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manifest_path, target)
        shutil.copyfile(ROOT / '.gitattributes', self.root / '.gitattributes')
        for name in ('verify_stage.py', 'test_exact_stage.py', 'README.md'):
            shutil.copyfile(ROOT / 'reconstruction/mayhem' / name, self.root / 'reconstruction/mayhem' / name)
        self.output = Path(self.temporary.name) / 'real stage output'

    def stage(self):
        return subprocess.run([sys.executable, '-B', str(self.root / 'programs/mayhem/build_exact.py'),
                               '--stage-only', '--repo', str(self.root), '--output', str(self.output)],
                              text=True, capture_output=True,
                              env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))

    def test_complete_real_stage(self):
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob('*') if p.is_file()}
        result = self.stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Validated 67 current source files', result.stdout)
        checked = verify(self.root, self.output)
        self.assertEqual((checked['source_files'], checked['recipe_files']), (67, 98))
        self.assertFalse((self.output / 'build').exists())
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_original_missing_input_failure(self):
        (self.root / 'research/mayhem-linker-locators-20261028/inputs.json').unlink()
        result = self.stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('inputs.json', result.stderr)
        self.assertFalse(self.output.exists())

    def test_three_sealed_input_mutations_rejected_before_stage(self):
        pins = json.loads((self.root / 'research/mayhem-linker-locators-20261028/inputs.json').read_text())
        for name, message in [(pins['source_builder_parent'], 'sealed source stager changed'),
                              (pins['parent_script'], 'sealed linker script changed'),
                              ('research/mayhem-linker-locators-20261028/ordered-native.ld', 'derived linker script changed')]:
            with self.subTest(path=name):
                p = self.root / name
                original = p.read_bytes()
                try:
                    p.write_bytes(original + b'\n')
                    result = self.stage()
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(message, result.stderr)
                    self.assertFalse(self.output.exists())
                finally:
                    p.write_bytes(original)

    def test_canonical_rust_change_rejected(self):
        source = self.root / 'programs/mayhem/src/state.rs'
        source.write_bytes(source.read_bytes() + b'\n')
        result = self.stage()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('current Mayhem inputs differ', result.stderr)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_not_overwritten(self):
        result = self.stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        snapshot = {p.relative_to(self.output).as_posix(): p.read_bytes()
                    for p in self.output.rglob('*') if p.is_file()}
        repeated = self.stage()
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn('FileExistsError', repeated.stderr)
        self.assertEqual(snapshot, {p.relative_to(self.output).as_posix(): p.read_bytes()
                                    for p in self.output.rglob('*') if p.is_file()})

    def test_archive_mutation_fails_public_blob_authentication(self):
        archive = self.root / 'research/mayhem-fresh-host-20261028/host-inputs/archives/cargo_toml-0.19.2.crate'
        archive.write_bytes(archive.read_bytes() + b'X')
        with self.assertRaisesRegex(ValueError, 'restored bytes differ'):
            verify(self.root)

    def test_recovery_manifest_cannot_reseal_a_mutation(self):
        manifest = self.root / 'reconstruction/mayhem/recovered-stage-inputs.json'
        document = json.loads(manifest.read_text())
        document['files'][0]['sha256'] = '0' * 64
        manifest.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'recovery manifest changed'):
            verify(self.root)

    def test_original_checkout_policy_preserves_crlf_with_autocrlf(self):
        checkout = self.root
        manifest = json.loads((self.root / 'reconstruction/mayhem/recovered-stage-inputs.json').read_text())
        prefix = 'research/mayhem-fresh-host-20261028/'
        expected = {p.relative_to(checkout).as_posix(): p.read_bytes() for p in checkout.rglob('*')
                    if p.is_file() and p != checkout / '.gitattributes'}
        for name in ['controller/historical-macro.json', 'controller/source-inputs.json',
                     'host-inputs/supplement-packages.json']:
            self.assertIn(b'\r\n', expected[prefix + name])
        def git(*args):
            return subprocess.run(['git', '-c', 'core.autocrlf=true', '-C', str(checkout), *args],
                                  text=True, capture_output=True, check=True)
        git('init', '-q')
        git('add', '.')
        for name, data in expected.items():
            staged = subprocess.check_output(['git', '-C', str(checkout), 'show', ':' + name])
            self.assertEqual(staged, data)
            (checkout / name).unlink()
        git('checkout-index', '--all', '--force')
        changed = [name for name, data in expected.items() if (checkout / name).read_bytes() != data]
        self.assertEqual(changed, [], 'checkout changed sealed/canonical bytes: ' + repr(changed))
        result = self.stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(verify(checkout, self.output)['source_files'], 67)


if __name__ == '__main__':
    unittest.main()
