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
    def test_real_mixed_case_package_uses_lowercase_index_path(self):
        fixture = Path(__file__).with_name('fixtures') / 'cargo-index-case'
        archive_bytes = (fixture / 'Inflector-0.11.4.crate').read_bytes()
        index_bytes = (fixture / 'inflector-index.jsonl').read_bytes()
        digest = hashlib.sha256(archive_bytes).hexdigest()
        self.assertEqual(digest, 'fe438c63458706e03479442743baae6c88256498e6431708f6dfc520a26515d3')
        self.assertEqual(hashlib.sha256(index_bytes).hexdigest(), 'cb2b8f9cd2baa2934fa604108cd792b30f83b4ba32de329607046984d2213957')
        rows = [(json.loads(line), line) for line in index_bytes.splitlines()]
        selected = [record for record, _ in rows if record['vers'] == '0.11.4']
        self.assertEqual(len(selected), 1)
        self.assertEqual((selected[0]['name'], selected[0]['cksum']), ('Inflector', digest))
        cache_bytes = b'\x03\x02\x00\x00\x00offline-fixture\x00' + b''.join(
            record['vers'].encode('utf-8') + b'\x00' + raw + b'\x00' for record, raw in rows)
        namespaces = ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f')
        for namespace in namespaces:
            with self.subTest(namespace=namespace), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                home = root / 'home'
                archive = home / 'registry/cache' / namespace / 'Inflector-0.11.4.crate'
                archive.parent.mkdir(parents=True)
                archive.write_bytes(archive_bytes)
                index = home / 'registry/index' / namespace / '.cache/in/fl/inflector'
                index.parent.mkdir(parents=True)
                index.write_bytes(cache_bytes)
                (home / 'registry/index' / namespace / 'config.json').write_text(
                    '{"dl":"https://static.crates.io/crates","api":"https://crates.io"}', encoding='utf-8')
                lock = root / 'Cargo.lock'
                lock.write_text('version = 3\n[[package]]\nname="Inflector"\nversion="0.11.4"\n'
                                'source="registry+https://github.com/rust-lang/crates.io-index"\n'
                                f'checksum="{digest}"\n', encoding='utf-8')
                output = root / 'output'
                result = subprocess.run([sys.executable, str(Path(__file__).with_name('prepare_locked_cargo_home.py')),
                                         '--lockfile', str(lock), '--output', str(output)],
                                        env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                paths = {path.relative_to(output).as_posix() for path in output.rglob('*') if path.is_file()}
                for target in namespaces:
                    canonical = f'registry/index/{target}/.cache/in/fl/inflector'
                    self.assertIn(canonical, paths)  # Also detects spelling errors on case-insensitive hosts.
                    self.assertEqual((output / canonical).read_bytes(), cache_bytes)
                    self.assertEqual((output / 'registry/cache' / target / archive.name).read_bytes(), archive_bytes)

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
