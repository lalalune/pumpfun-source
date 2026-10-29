"""Run the assembler on tiny synthetic toolchains, never a real compiler."""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('make_hybrid144.sh')


@unittest.skipUnless(sys.platform == 'darwin', 'assembler uses macOS clone-copy options')
class HybridStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mac = self.root / 'mac/rust'
        self.linux = self.root / 'linux'
        self.out = self.root / 'installed'
        (self.mac / 'bin').mkdir(parents=True)
        (self.mac / 'lib/rustlib/aarch64-apple-darwin').mkdir(parents=True)
        rustc = self.mac / 'bin/rustc'
        rustc.write_text('#!/bin/sh\ncd "$(dirname "$0")/.." && pwd -P\n')
        rustc.chmod(0o755)
        for name in ('librustc_driver-fixture.dylib', 'libstd-fixture.dylib'):
            (self.mac / 'lib' / name).write_bytes(b'fixture')
        self.lib = self.linux / 'rust/lib/rustlib/sbpf-solana-solana/lib/libcore-fixture.rlib'
        self.lib.parent.mkdir(parents=True)
        self.lib.write_bytes(b'library')
        (self.linux / 'version.md').write_text('fixture v1.44\n')
        self.manifest = self.root / 'checksums'
        self.manifest.write_text(hashlib.sha256(b'library').hexdigest() + '  sbpf-solana-solana/lib/libcore-fixture.rlib\n')
        self.out.mkdir()
        (self.out / 'previous').write_bytes(b'previous toolchain')

    def run_assembler(self):
        return subprocess.run(['bash', str(SCRIPT), str(self.out), str(self.mac), str(self.linux), str(self.manifest)],
                              capture_output=True, text=True)

    def assert_preserved(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.out / 'previous').read_bytes(), b'previous toolchain')
        self.assertEqual(list(self.root.glob('installed.stage.*')), [])

    def test_checksum_failure_preserves_previous_toolchain(self):
        self.lib.write_bytes(b'wrong library')
        self.assert_preserved(self.run_assembler())

    def test_missing_input_preserves_previous_toolchain(self):
        (self.mac / 'lib/libstd-fixture.dylib').unlink()
        self.assert_preserved(self.run_assembler())

    def test_failed_compiler_probe_preserves_previous_toolchain(self):
        (self.mac / 'bin/rustc').write_text('#!/bin/sh\nexit 3\n')
        self.assert_preserved(self.run_assembler())

    def test_success_publishes_verified_bytes_and_cleans_staging(self):
        result = self.run_assembler()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.out / 'previous').exists())
        library = self.out / 'rust/lib/rustlib/sbpf-solana-solana/lib/libcore-fixture.rlib'
        self.assertEqual(library.read_bytes(), b'library')
        self.assertEqual(os.readlink(self.out / 'rust/lib/rustlib/aarch64-apple-darwin'),
                         str(self.mac.resolve() / 'lib/rustlib/aarch64-apple-darwin'))
        self.assertIn(str(self.out.resolve() / 'rust'), result.stdout)
        self.assertEqual(list(self.root.glob('installed.stage.*')), [])
        self.assertEqual(list(self.root.glob('installed.backup.*')), [])


if __name__ == '__main__':
    unittest.main()
