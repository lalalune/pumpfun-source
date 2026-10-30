"""Historical package inventories use the sealed manifest's POSIX keys."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_supported_sbpf_history as bridge


class HistoricalPackagePathsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'input'
        self.view = Path(temporary.name) / 'view'
        self.view.mkdir()
        self.package = Path('repro/build-tooling/example')
        # A small package fixture, not compiler output or a runtime receipt.
        self.files = {'README.md': b'fixture\n',
                      'source/programs/example/src/lib.rs': b'pub fn example() {}\n'}
        for name, data in self.files.items():
            path = self.root / self.package / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest = {name: hashlib.sha256(data).hexdigest()
                    for name, data in self.files.items()}
        self.manifest = json.dumps(manifest, sort_keys=True).encode()
        (self.root / self.package / 'manifest.json').write_bytes(self.manifest)
        self.seal = hashlib.sha256(self.manifest).hexdigest()

    def stage(self):
        bridge.stage_package(self.root, self.view, self.package, self.seal)

    def test_nested_manifest_keys_stage_exact_package_bytes(self):
        self.stage()
        for name, data in {**self.files, 'manifest.json': self.manifest}.items():
            self.assertEqual((self.view / self.package / name).read_bytes(), data)

    def test_unlisted_file_is_rejected_before_publication(self):
        (self.root / self.package / 'extra.txt').write_bytes(b'extra')
        with self.assertRaises(AssertionError):
            self.stage()
        self.assertEqual(list(self.view.iterdir()), [])

    def test_missing_nested_file_is_rejected_before_publication(self):
        (self.root / self.package / 'source/programs/example/src/lib.rs').unlink()
        with self.assertRaises(AssertionError):
            self.stage()
        self.assertEqual(list(self.view.iterdir()), [])

    def test_changed_nested_bytes_are_rejected(self):
        (self.root / self.package / 'source/programs/example/src/lib.rs').write_bytes(b'changed')
        with self.assertRaises(AssertionError):
            self.stage()


if __name__ == '__main__':
    unittest.main()
