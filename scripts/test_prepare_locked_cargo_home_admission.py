"""Unresolvable locked packages must be refused before the cache is created."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('prepare_locked_cargo_home.py')
CRATES_IO = 'registry+https://github.com/rust-lang/crates.io-index'
NAMESPACE = 'index.crates.io-1949cf8c6b5b557f'


class LockedCacheAdmissionTests(unittest.TestCase):
    def prepare(self, missing_archive=False, missing_config=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / 'cargo-home'
            archive = home / 'registry/cache' / NAMESPACE / 'cache-probe-1.0.0.crate'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'isolated archive')
            index = home / 'registry/index' / NAMESPACE / '.cache/ca/ch/cache-probe'
            index.parent.mkdir(parents=True)
            index.write_bytes(b'isolated sparse index')
            if not missing_config:
                (home / 'registry/index' / NAMESPACE / 'config.json').write_text('{}', encoding='utf-8')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            lock = f'[[package]]\nname="cache-probe"\nversion="1.0.0"\nsource="{CRATES_IO}"\nchecksum="{digest}"\n'
            if missing_archive:
                # Sorted after the resolvable package, as Cargo.lock orders entries.
                lock += f'[[package]]\nname="zz-absent"\nversion="1.0.0"\nsource="{CRATES_IO}"\nchecksum="{"0" * 64}"\n'
            (root / 'Cargo.lock').write_text(lock, encoding='utf-8')
            output = root / 'output'
            result = subprocess.run([sys.executable, str(SCRIPT), '--lockfile', str(root / 'Cargo.lock'),
                                     '--output', str(output)],
                                    env={**os.environ, 'CARGO_HOME': str(home)}, capture_output=True, text=True)
            return result, output.exists()

    def test_missing_later_archive_creates_no_partial_cache(self):
        result, created = self.prepare(missing_archive=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No checksum-verified cached archive: zz-absent-1.0.0.crate', result.stderr)
        self.assertFalse(created, 'a partial cache blocks the documented rerun (exist_ok=False)')

    def test_missing_registry_configuration_creates_no_partial_cache(self):
        result, created = self.prepare(missing_config=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No local crates.io registry configuration', result.stderr)
        self.assertFalse(created)

    def test_resolvable_lockfile_still_prepares_cache(self):
        result, created = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(created)


if __name__ == '__main__':
    unittest.main()
