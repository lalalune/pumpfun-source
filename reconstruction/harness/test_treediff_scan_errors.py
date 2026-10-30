import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from treediff import tree_diff, tree_files


class TreeScanErrors(unittest.TestCase):
    def test_disappearing_child_cannot_become_a_deletion_patch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, changed = root/'base', root/'changed'
            for source in (base, changed):
                (source/'src').mkdir(parents=True)
                (source/'src/lib.rs').write_bytes(b'pub const VALUE: u8 = 7;\n')
            real_scan = os.scandir
            moved = False
            def scan(path):
                nonlocal moved
                if Path(path) == changed/'src' and not moved:
                    moved = True
                    (changed/'src').rename(root/'moved-source')
                return real_scan(path)
            with patch.object(os, 'scandir', scan):
                with self.assertRaises(FileNotFoundError):
                    tree_diff(base, changed)
            self.assertTrue(moved)
            self.assertEqual((root/'moved-source/lib.rs').read_bytes(), b'pub const VALUE: u8 = 7;\n')

    def test_disappearing_root_cannot_become_an_empty_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root/'source'; source.mkdir()
            (source/'lib.rs').write_bytes(b'fn main() {}\n')
            real_scan = os.scandir
            moved = False
            def scan(path):
                nonlocal moved
                if Path(path) == source and not moved:
                    moved = True
                    source.rename(root/'moved-source')
                return real_scan(path)
            with patch.object(os, 'scandir', scan):
                with self.assertRaises(FileNotFoundError):
                    tree_files(source)
            self.assertTrue(moved)

    def test_stable_nested_tree_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'empty').mkdir()
            (root/'src').mkdir()
            (root/'src/lib.rs').write_bytes(b'fn main() {}\n')
            self.assertEqual(tree_files(root), {'src/lib.rs': b'fn main() {}\n'})


if __name__ == '__main__': unittest.main()
