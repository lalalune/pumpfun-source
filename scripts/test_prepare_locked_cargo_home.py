"""Exercise cache preparation against an isolated Cargo home without network access."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CargoHomeTests(unittest.TestCase):
    def test_path_only_lockfile_needs_no_registry_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / 'Cargo.lock'
            lock.write_text('version = 3\n[[package]]\nname = "local-only"\nversion = "1.0.0"\n', encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(root / 'absent-cargo-home')}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_text())
            self.assertEqual(manifest['packages'], [])
            self.assertIsNone(manifest['registry_config_sha256'])
            self.assertEqual(manifest['lockfile_sha256'], hashlib.sha256(lock.read_bytes()).hexdigest())
            self.assertFalse((output / 'registry').exists())

    def test_supported_cache_namespaces_supply_configuration(self):
        for namespace in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
            with self.subTest(namespace=namespace):
                self.prepare_from_namespace(namespace)

    def test_alternative_registry_is_rejected_before_output_creation(self):
        self.prepare_from_namespace(
            'index.crates.io-1949cf8c6b5b557f',
            registry_source='registry+https://registry.example.invalid/index',
            rejected=True,
        )

    def prepare_from_namespace(self, namespace,
                               registry_source='registry+https://github.com/rust-lang/crates.io-index',
                               rejected=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            archive = home / 'registry/cache' / namespace / 'cache-probe-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'isolated archive')
            index = home / 'registry/index' / namespace / '.cache/ca/ch/cache-probe'
            index.parent.mkdir(parents=True)
            index.write_bytes(b'isolated sparse index')
            config = index.parents[3] / 'config.json'
            config.write_text('{}', encoding='utf-8')
            lock = root / 'Cargo.lock'
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            lock.write_text('[[package]]\nname="cache-probe"\nversion="1.0.0"\n'
                            f'source="{registry_source}"\n'
                            f'checksum="{digest}"\n', encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                     '--lockfile', str(lock), '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            if rejected:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Unsupported registry source', result.stderr)
                self.assertFalse(output.exists())
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads((output / 'cache-manifest.json').read_text())
            self.assertEqual(manifest['packages'][0]['archive_sha256'], digest)
            for target in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
                self.assertEqual((output / 'registry/cache' / target / archive.name).read_bytes(), archive.read_bytes())
                self.assertEqual((output / 'registry/index' / target / '.cache/ca/ch/cache-probe').read_bytes(), index.read_bytes())


if __name__ == '__main__':
    unittest.main()
