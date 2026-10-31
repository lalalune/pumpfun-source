"""Exercise macOS hybrid admission with real files, without a compiler download."""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap


class MacHybridTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sdk = self.root / 'sdk'
        self.cache = self.root / 'cache'
        self.hybrid = self.cache / 'toolchains/hybrid144'
        rustc = self.sdk / 'rust/bin/rustc'
        rustc.parent.mkdir(parents=True)
        # Only the bootstrap sysroot probe executes; this is not a Rust compiler.
        rustc.write_text('#!/bin/sh\ncd "$(dirname "$0")/.." && pwd -P\n')
        rustc.chmod(0o755)
        (self.sdk / 'rust/lib/rustlib/aarch64-apple-darwin').mkdir(parents=True)
        for name in ('librustc_driver-fixture.dylib', 'libstd-fixture.dylib'):
            (self.sdk / 'rust/lib' / name).write_bytes(name.encode())
        inventory = {path.relative_to(self.sdk).as_posix(): {
            'type': 'file', 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        } for path in self.sdk.rglob('*') if path.is_file()}
        (self.root / 'v1.44-macos-inventory.json').write_text(json.dumps({'entries': inventory}))
        self.linux = self.root / 'linux'
        self.relative = Path('rust/lib/rustlib/sbpf-solana-solana/lib/libcore-fixture.rlib')
        library = self.linux / self.relative
        library.parent.mkdir(parents=True)
        library.write_bytes(b'target library')
        (self.linux / 'version.md').write_text('fixture v1.44\n')
        manifest = self.root / 'manifest'
        manifest.write_text(hashlib.sha256(library.read_bytes()).hexdigest()
                            + '  sbpf-solana-solana/lib/libcore-fixture.rlib\n')
        for name, value in (('HERE', self.root), ('SDK', self.sdk), ('LINUX', self.linux),
                            ('MANIFEST', manifest), ('HOME_CACHE', self.cache),
                            ('HYBRID', self.hybrid), ('HOST_PLATFORM', 'darwin')):
            override = patch.object(bootstrap, name, value)
            override.start()
            self.addCleanup(override.stop)

    def install_fixture(self):
        shutil.copytree(self.sdk / 'rust', self.hybrid / 'rust')
        host = self.hybrid / 'rust/lib/rustlib/aarch64-apple-darwin'
        host.rmdir()
        host.symlink_to(self.sdk / 'rust/lib/rustlib/aarch64-apple-darwin')
        shutil.copytree(self.linux / 'rust/lib/rustlib/sbpf-solana-solana',
                        self.hybrid / 'rust/lib/rustlib/sbpf-solana-solana')

    def run_bootstrap(self):
        with patch.object(sys, 'argv', ['bootstrap.py', '--sdk-check', 'full']):
            return bootstrap.main()

    def test_existing_hybrid_is_verified_and_reused(self):
        self.install_fixture()
        marker = self.hybrid / 'retained'
        marker.write_bytes(b'existing installation')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(self.run_bootstrap(), 0)
        self.assertIn('hybrid144 already assembled', output.getvalue())
        self.assertEqual(marker.read_bytes(), b'existing installation')
        self.assertTrue((self.cache / 'locks').is_dir())

    def test_target_library_changes_are_rejected(self):
        self.install_fixture()
        library = self.hybrid / self.relative
        for changed in (b'changed library', None):
            with self.subTest(changed=changed):
                if changed is None:
                    library.unlink()
                else:
                    library.write_bytes(changed)
                self.assertFalse(bootstrap.hybrid_ok())
        shutil.copy2(self.linux / self.relative, library)
        (library.parent / 'libextra.rlib').write_bytes(b'extra input')
        self.assertFalse(bootstrap.hybrid_ok())

    def test_replaced_host_library_names_reject_cache_without_aborting(self):
        self.install_fixture()
        library_dir = self.hybrid / 'rust/lib'
        for name in ('librustc_driver-fixture.dylib', 'libstd-fixture.dylib'):
            with self.subTest(library=name):
                library = library_dir / name
                stale = library_dir / 'libstale-fixture.dylib'
                library.rename(stale)
                try:
                    self.assertFalse(bootstrap.hybrid_ok())
                finally:
                    stale.rename(library)
        self.assertTrue(bootstrap.hybrid_ok())

    @unittest.skipUnless(sys.platform == 'darwin', 'assembly uses macOS clone-copy options')
    def test_native_assembly_is_verified_and_reused(self):
        self.assertEqual(self.run_bootstrap(), 0)
        self.assertTrue(bootstrap.hybrid_ok())
        self.assertEqual((self.hybrid / self.relative).read_bytes(), b'target library')
        marker = self.hybrid / 'retained'
        marker.write_bytes(b'existing installation')
        self.assertEqual(self.run_bootstrap(), 0)
        self.assertEqual(marker.read_bytes(), b'existing installation')


if __name__ == '__main__':
    unittest.main()
