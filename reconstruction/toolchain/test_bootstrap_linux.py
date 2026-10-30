"""Assemble the identity toolchain for a Linux v1.44 host; no real compiler needed.

The macOS inventory cannot certify the Linux platform-tools archive, so these
tests pin the behaviour a Linux checkout needs: a valid archive is accepted,
identified by the compiler revision and the target libraries, and assembled into
$PUMP_RECON_HOME/toolchains/hybrid144 in the layout harness/fastbuild.py reads.
"""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap

TRIPLE = 'x86_64-unknown-linux-gnu'
REVISION = '08b7341888ab480dfaaa0698300cbbbbb2d75b53'


def digest(data):
    return hashlib.sha256(data).hexdigest()


class LinuxToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / 'cache'
        self.sdk = self.root / 'sdk'
        # A stub compiler that answers the single sysroot query bootstrap makes,
        # so the assembler runs for real without a 134 MB toolchain in the fixture.
        self.rustc = self.sdk / 'rust/bin/rustc'
        self.rustc.parent.mkdir(parents=True)
        self.rustc.write_text('#!/bin/sh\n'
                              'case "$1" in\n'
                              '  --print) cd "$(dirname "$0")/.." && pwd -P ;;\n'
                              'esac\n')
        self.rustc.chmod(0o755)
        (self.sdk / 'rust/lib').mkdir(parents=True)
        (self.sdk / 'rust/lib/libstd-example.so').write_bytes(b'host standard library')
        host_lib = self.sdk / 'rust/lib/rustlib' / TRIPLE / 'lib'
        host_lib.mkdir(parents=True)
        (host_lib / 'libcore-host.rlib').write_bytes(b'host core')
        self.sdk_lib = self.sdk / 'rust/lib/rustlib/sbpf-solana-solana/lib'
        self.sdk_lib.mkdir(parents=True)
        (self.sdk_lib / 'libcore-target.rlib').write_bytes(b'target core')
        self.version = self.sdk / 'version.md'
        self.version.write_text(f'{REVISION}  https://github.com/anza-xyz/rust.git\n')
        # The tracked Linux tree carries the same target library as the archive.
        self.linux = self.root / 'linux-v1.44-x86_64'
        tracked = self.linux / 'rust/lib/rustlib/sbpf-solana-solana/lib'
        tracked.mkdir(parents=True)
        (tracked / 'libcore-target.rlib').write_bytes(b'target core')
        (tracked / 'self-contained').mkdir()
        self.manifest = self.root / 'manifest'
        self.manifest.write_text(f"{digest(b'target core')}  sbpf-solana-solana/lib/libcore-target.rlib\n")
        self.hybrid = self.cache / 'toolchains/hybrid144'
        for name, value in (('SDK', self.sdk), ('LINUX', self.linux), ('MANIFEST', self.manifest),
                            ('HOME_CACHE', self.cache), ('HYBRID', self.hybrid)):
            self.override(name, value)
        self.override('HOST_PLATFORM', 'linux')
        self.override('HOST_MACHINE', 'x86_64')

    def override(self, name, value):
        patcher = patch.object(bootstrap, name, value, create=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_bootstrap(self, *args):
        with patch.object(sys, 'argv', ['bootstrap.py', *args]):
            return bootstrap.main()

    def test_bootstrap_assembles_the_identity_toolchain(self):
        self.assertEqual(self.run_bootstrap('--sdk-check', 'quick'), 0)
        self.assertTrue((self.hybrid / 'rust/bin/rustc').is_file())
        host = self.hybrid / f'rust/lib/rustlib/{TRIPLE}'
        self.assertTrue(host.is_symlink())
        self.assertEqual(host.resolve(), (self.sdk / f'rust/lib/rustlib/{TRIPLE}').resolve())
        copied = self.hybrid / 'rust/lib/rustlib/sbpf-solana-solana/lib/libcore-target.rlib'
        self.assertEqual(copied.read_bytes(), b'target core')
        self.assertTrue((copied.parent / 'self-contained').is_dir())
        self.assertEqual((self.hybrid / 'version.md').read_text().split()[0], REVISION)
        self.assertTrue(bootstrap.hybrid_ok_linux())
        # A second run finds the assembled toolchain and changes nothing.
        self.assertEqual(self.run_bootstrap('--sdk-check', 'quick'), 0)

    def test_full_check_accepts_the_archive(self):
        self.assertEqual(bootstrap.check_sdk_linux('full'), [])
        self.assertEqual(self.run_bootstrap('--sdk-check', 'full'), 0)

    def test_stale_toolchain_is_replaced(self):
        stale = self.hybrid / 'rust/bin/rustc'
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b'old compiler')
        self.assertEqual(self.run_bootstrap('--sdk-check', 'quick'), 0)
        self.assertTrue(bootstrap.hybrid_ok_linux())

    def test_foreign_revision_is_rejected(self):
        self.version.write_text('0' * 40 + '  https://github.com/anza-xyz/rust.git\n')
        self.assertIn(f'rust revision is not {REVISION}', bootstrap.check_sdk_linux('quick'))
        self.assertEqual(self.run_bootstrap('--sdk-check', 'quick'), 1)
        self.assertFalse(self.hybrid.exists())

    def test_missing_compiler_is_rejected(self):
        self.rustc.unlink()
        self.assertIn('missing rust/bin/rustc', bootstrap.check_sdk_linux('quick'))
        self.assertEqual(self.run_bootstrap('--sdk-check', 'quick'), 1)

    def test_missing_host_libraries_are_rejected(self):
        base = self.sdk / 'rust/lib/rustlib' / TRIPLE
        (base / 'lib/libcore-host.rlib').unlink()
        (base / 'lib').rmdir()
        base.rmdir()
        self.assertIn(f'missing rust/lib/rustlib/{TRIPLE}', bootstrap.check_sdk_linux('quick'))

    def test_changed_and_unlisted_target_libraries_are_rejected(self):
        (self.sdk_lib / 'libcore-target.rlib').write_bytes(b'changed')
        problems = bootstrap.check_sdk_linux('full')
        self.assertIn('SDK sbpf-solana-solana/lib/libcore-target.rlib', problems)
        (self.sdk_lib / 'libcore-target.rlib').write_bytes(b'target core')
        self.assertEqual(bootstrap.check_sdk_linux('full'), [])
        (self.sdk_lib / 'libextra-target.rlib').write_bytes(b'extra')
        self.assertIn('SDK unexpected library input: sbpf-solana-solana/lib/libextra-target.rlib',
                      bootstrap.check_sdk_linux('full'))

    def test_unsupported_host_is_refused(self):
        self.override('HOST_PLATFORM', 'win32')
        self.assertEqual(self.run_bootstrap('--sdk-check', 'skip'), 1)

    def test_unsupported_linux_machine_is_refused(self):
        self.override('HOST_MACHINE', 'aarch64')
        self.assertEqual(self.run_bootstrap('--sdk-check', 'skip'), 1)


if __name__ == '__main__':
    unittest.main()