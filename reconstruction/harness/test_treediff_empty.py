"""Generated patches must reproduce empty-file additions and removals."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from treediff import tree_diff


class EmptyFilePatchTests(unittest.TestCase):
    def roundtrip(self, old, new):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base, candidate, checkout = (root / name for name in ('base', 'new', 'checkout'))
            for folder in (base, candidate, checkout / 'programs/pump'):
                folder.mkdir(parents=True)
            for name, data in old.items():
                (base / name).write_bytes(data)
                (checkout / 'programs/pump' / name).write_bytes(data)
            for name, data in new.items():
                (candidate / name).write_bytes(data)
            patch = tree_diff(base, candidate)
            self.assertTrue(patch)
            result = subprocess.run(['git', 'apply', '-'], cwd=checkout,
                                    input=patch, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = {p.name: p.read_bytes() for p in (checkout / 'programs/pump').glob('*')}
            self.assertEqual(actual, new)

    def test_empty_addition(self):
        self.roundtrip({}, {'empty.rs': b''})

    def test_empty_deletion(self):
        self.roundtrip({'empty.rs': b''}, {})

    def test_mixed_empty_and_text_changes(self):
        self.roundtrip({'gone.rs': b'', 'keep.rs': b'old\n'},
                       {'new.rs': b'', 'keep.rs': b'new\n'})


if __name__ == '__main__':
    unittest.main()
