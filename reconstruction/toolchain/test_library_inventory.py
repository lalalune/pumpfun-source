"""Verify exact library inputs using temporary fixtures and the retained inventory."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap


class LibraryInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lib = self.root / 'rust/lib/rustlib/sbpf-solana-solana/lib'
        self.lib.mkdir(parents=True)
        self.file = self.lib / 'libcore-example.rlib'
        self.file.write_bytes(b'library fixture')
        self.digest = hashlib.sha256(self.file.read_bytes()).hexdigest()
        self.record = f'{self.digest}  sbpf-solana-solana/lib/{self.file.name}\n'
        self.manifest = self.root / 'manifest'
        self.manifest.write_text(self.record)
        self.override = patch.object(bootstrap, 'MANIFEST', self.manifest)
        self.override.start()
        self.addCleanup(self.override.stop)

    def test_exact_set_and_empty_self_contained_directory(self):
        (self.lib / 'self-contained').mkdir()
        self.assertEqual(bootstrap.check_linux_libs(self.root), [])

    def test_extra_library_is_rejected(self):
        (self.lib / 'libcore-other.rlib').write_bytes(b'other build')
        self.assertIn('unexpected library input', '\n'.join(bootstrap.check_linux_libs(self.root)))

    def test_changed_and_missing_library_are_rejected(self):
        self.file.write_bytes(b'changed')
        self.assertTrue(bootstrap.check_linux_libs(self.root))
        self.file.unlink()
        self.assertTrue(bootstrap.check_linux_libs(self.root))

    def test_manifest_must_be_nonempty_unique_and_canonical(self):
        for text in ('', self.record * 2, 'bad record\n',
                     f'{self.digest}  ../outside.rlib\n',
                     f'{self.digest}  /absolute.rlib\n'):
            with self.subTest(text=text):
                self.manifest.write_text(text)
                self.assertTrue(bootstrap.check_linux_libs(self.root))

    def test_symlink_library_is_not_an_owned_inventory_file(self):
        outside = self.root / 'external'
        outside.write_bytes(self.file.read_bytes())
        self.file.unlink()
        self.file.symlink_to(outside)
        self.assertTrue(bootstrap.check_linux_libs(self.root))

    def test_directory_alias_is_rejected(self):
        saved = self.lib.with_name('saved')
        self.lib.rename(saved)
        self.lib.symlink_to(saved, target_is_directory=True)
        self.assertEqual(bootstrap.check_linux_libs(self.root), ['target library directory is a symlink'])


class RetainedInventoryTest(unittest.TestCase):
    def test_all_retained_libraries_verify(self):
        self.assertEqual(bootstrap.check_linux_libs(bootstrap.LINUX), [])


class SdkInventoryTests(unittest.TestCase):
    def test_sdk_scan_error_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sdk = root / 'sdk'
            library = sdk / 'rust/lib/rustlib/aarch64-apple-darwin/lib'
            library.mkdir(parents=True)
            known = library / 'libknown.rlib'
            known.write_bytes(b'known library')
            (library / 'libhidden.rlib').write_bytes(b'hidden library')
            rel = known.relative_to(sdk).as_posix()
            (root / 'v1.44-macos-inventory.json').write_text(json.dumps({'entries': {
                rel: {'type': 'file', 'bytes': known.stat().st_size,
                      'sha256': hashlib.sha256(known.read_bytes()).hexdigest()}
            }}))
            real_scandir = os.scandir

            def unreadable(path):
                if Path(path) == library:
                    raise PermissionError('synthetic SDK scan failure')
                return real_scandir(path)

            with patch.object(bootstrap, 'HERE', root), patch.object(bootstrap, 'SDK', sdk), \
                    patch.object(os, 'scandir', side_effect=unreadable):
                self.assertIn('SDK traversal:', '\n'.join(bootstrap.check_sdk('full')[1]))

    def test_recorded_dangling_link_and_unlisted_directory_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sdk = root / 'sdk'
            sdk.mkdir()
            recorded = sdk / 'recorded-link'
            recorded.symlink_to('absent-target')
            (root / 'v1.44-macos-inventory.json').write_text(json.dumps({'entries': {
                'recorded-link': {'type': 'symlink', 'target': 'absent-target'}
            }}))
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'unlisted.rlib').write_bytes(b'outside')
            with patch.object(bootstrap, 'HERE', root), patch.object(bootstrap, 'SDK', sdk):
                self.assertEqual(bootstrap.check_sdk('full'), (1, []))
                (sdk / 'unlisted-dir').symlink_to(outside, target_is_directory=True)
                problems = bootstrap.check_sdk('quick')[1]
                self.assertIn('unexpected SDK input: unlisted-dir', problems)
                self.assertEqual(len(problems), 1)

    def test_unlisted_host_library_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sdk = root / 'sdk'
            host_lib = sdk / 'rust/lib/rustlib/aarch64-apple-darwin/lib'
            host_lib.mkdir(parents=True)
            known = host_lib / 'libknown.rlib'
            known.write_bytes(b'known library')
            inventory = root / 'v1.44-macos-inventory.json'
            rel = known.relative_to(sdk).as_posix()
            inventory.write_text(json.dumps({'entries': {
                rel: {'type': 'file', 'bytes': known.stat().st_size,
                      'sha256': hashlib.sha256(known.read_bytes()).hexdigest()}
            }}))
            with patch.object(bootstrap, 'HERE', root), patch.object(bootstrap, 'SDK', sdk):
                self.assertEqual(bootstrap.check_sdk('full'), (1, []))
                extra = host_lib / 'libunlisted.rlib'
                extra.write_bytes(b'unlisted library')
                self.assertIn('unexpected SDK input: ' + extra.relative_to(sdk).as_posix(),
                              bootstrap.check_sdk('full')[1])
                extra.unlink()
                extra.symlink_to(known.name)
                self.assertIn('unexpected SDK input: ' + extra.relative_to(sdk).as_posix(),
                              bootstrap.check_sdk('quick')[1])


if __name__ == '__main__':
    unittest.main()
