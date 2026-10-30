"""Apply generated source patches with Git and compare the resulting bytes."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from treediff import tree_diff


@unittest.skipUnless(shutil.which('git'), 'Git is required for patch round trips')
class TreeDiffTests(unittest.TestCase):
    def assert_round_trip(self, before, after):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, new, checkout = (root / name for name in ('base', 'new', 'checkout'))
            target = checkout / 'programs/pump'
            for directory, files in ((base, before), (new, after), (target, before)):
                directory.mkdir(parents=True)
                for name, contents in files.items():
                    path = directory / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(contents)
            subprocess.run(['git', 'init', '--quiet', str(checkout)], check=True,
                           capture_output=True)
            patch = tree_diff(base, new).encode('utf-8')
            command = ['git', '-C', str(checkout), '-c', 'core.autocrlf=false', 'apply']
            for options in (['--check', '-'], ['-']):
                result = subprocess.run(command + options, input=patch, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
            actual = {p.relative_to(target).as_posix(): p.read_bytes()
                      for p in target.rglob('*') if p.is_file()}
            self.assertEqual(actual, after)

    def test_nested_modify_add_and_delete(self):
        self.assert_round_trip(
            {'src/lib.rs': b'mod old;\npub const VALUE: u64 = 1;\n',
             'src/old.rs': b'pub fn old() {}\n'},
            {'src/lib.rs': b'mod new;\npub const VALUE: u64 = 2;\n',
             'src/new.rs': b'pub fn new() {}\n'},
        )

    def test_nested_files_without_final_newline(self):
        self.assert_round_trip(
            {'src/nested/lib.rs': b'pub const VALUE: u64 = 1;'},
            {'src/nested/lib.rs': b'pub const VALUE: u64 = 2;'},
        )

    def test_crate_root_file(self):
        self.assert_round_trip(
            {'Cargo.toml': b'[package]\nname = "before"\n'},
            {'Cargo.toml': b'[package]\nname = "after"\n'},
        )


if __name__ == '__main__':
    unittest.main()
