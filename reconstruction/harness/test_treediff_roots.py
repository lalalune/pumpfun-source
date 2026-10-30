"""A missing source snapshot is not an intentionally empty source tree."""
from pathlib import Path
import tempfile
import unittest

from treediff import tree_diff, tree_files


class SourceRootTests(unittest.TestCase):
    def test_missing_candidate_is_not_a_delete_everything_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'lib.rs').write_text('fn main() {}\n')
            with self.assertRaises(FileNotFoundError):
                tree_diff(base, base / 'missing')

    def test_missing_base_is_not_an_add_everything_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory)
            (candidate / 'lib.rs').write_text('fn main() {}\n')
            with self.assertRaises(FileNotFoundError):
                tree_diff(candidate / 'missing', candidate)

    def test_regular_file_is_not_a_source_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'file.rs'
            source.write_text('source')
            with self.assertRaises(NotADirectoryError):
                tree_files(source)

    def test_existing_empty_tree_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(tree_files(directory), {})
            self.assertEqual(tree_diff(directory, directory), '')


if __name__ == '__main__':
    unittest.main()
