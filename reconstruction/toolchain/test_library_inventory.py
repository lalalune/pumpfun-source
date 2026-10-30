"""Verify exact library inputs using temporary fixtures and the retained inventory."""
import hashlib
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


if __name__ == '__main__':
    unittest.main()
