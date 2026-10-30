"""Real source-tree filesystem controls; no compiler or capture-byte changes."""
from pathlib import Path
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from treediff import tree_diff, tree_files


def directory_link(target, link):
    if sys.platform == 'win32':
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


class SourceTreeLinks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'base'; self.base.mkdir()
        self.part = self.root / 'part'; self.part.mkdir()
        self.separate = self.root / 'separate'; self.separate.mkdir()
        (self.separate / 'lib.rs').write_bytes(b'pub const SEPARATE: u32 = 7;\n')

    def test_nested_directory_link_cannot_supply_patch_contents(self):
        directory_link(self.separate, self.part / 'linked')
        with self.assertRaisesRegex(ValueError, 'source tree link'):
            tree_diff(self.base, self.part)
        self.assertEqual((self.separate / 'lib.rs').read_bytes(), b'pub const SEPARATE: u32 = 7;\n')

    def test_source_root_cannot_be_a_directory_link(self):
        link = self.root / 'source-root'
        directory_link(self.separate, link)
        with self.assertRaisesRegex(ValueError, 'source tree link'):
            tree_files(link)

    def test_dangling_directory_link_is_not_an_empty_tree(self):
        link = self.root / 'source-root'
        directory_link(self.separate, link)
        (self.separate / 'lib.rs').unlink()
        self.separate.rmdir()
        with self.assertRaisesRegex(ValueError, 'source tree link'):
            tree_files(link)

    def test_file_link_cannot_supply_patch_contents(self):
        link = self.part / 'lib.rs'
        try:
            link.symlink_to(self.separate / 'lib.rs')
        except OSError as error:
            if sys.platform == 'win32' and error.winerror == 1314:
                self.skipTest('Windows file-symlink privilege unavailable; real junction controls run separately')
            raise
        with self.assertRaisesRegex(ValueError, 'source tree link'):
            tree_diff(self.base, self.part)

    def test_regular_source_diff_and_order_are_unchanged(self):
        for root, value in [(self.base, b'7'), (self.part, b'8')]:
            (root / 'src').mkdir()
            (root / 'src/lib.rs').write_bytes(b'pub const VALUE: u32 = ' + value + b';\n')
            (root / 'Cargo.toml').write_bytes(b'[package]\nname = "tree-control"\n')
        self.assertEqual(list(tree_files(self.part)), sorted(tree_files(self.part)))
        diff = tree_diff(self.base, self.part)
        self.assertIn('-pub const VALUE: u32 = 7;\n', diff)
        self.assertIn('+pub const VALUE: u32 = 8;\n', diff)
        self.assertNotIn('Cargo.toml', diff)


if __name__ == '__main__':
    unittest.main()
