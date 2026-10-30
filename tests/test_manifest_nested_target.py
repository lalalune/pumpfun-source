"""Manifest real copied reconstruction source and explicitly supplied assets."""
import hashlib
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from build_source_manifest import source_manifest
from source_manifest_guard import strict_manifest


class NestedTargetInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='manifest-nested-target-')
        self.addCleanup(self.temporary.cleanup)
        # Resolve: on macOS the temp dir sits under the /var -> /private/var symlink.
        self.root = pathlib.Path(self.temporary.name).resolve()
        self.crate = self.root / 'crates/native-transfer-fee'
        shutil.copytree(ROOT / 'crates/native-transfer-fee', self.crate)
        self.source = self.crate / 'src/target/checkpoint.rs'
        self.source.parent.mkdir()
        # This exact retained source is selected by an explicit Rust module path.
        retained = (self.crate / 'src/lib.rs').read_bytes()
        self.source.write_bytes(retained.replace(b'#![no_std]\r\n', b'', 1).replace(b'#![no_std]\n', b'', 1))
        with (self.crate / 'src/lib.rs').open('ab') as lib:
            lib.write(b'\n#[path = "target/checkpoint.rs"]\npub mod checkpoint;\n')

    def manifest(self, *extras):
        return source_manifest(self.crate, self.crate, self.root, extras)

    def test_selected_nested_module_is_hash_bound(self):
        key = self.source.relative_to(self.root).as_posix()
        before = self.manifest()
        original = self.source.read_bytes()
        self.source.write_bytes(original.replace(
            b'const ONE_IN_BASIS_POINTS: u128 = 10_000;',
            b'const ONE_IN_BASIS_POINTS: u128 = 10_001;'))
        after = self.manifest()
        self.assertNotEqual(original, self.source.read_bytes())
        self.assertNotEqual(before, after)
        self.assertEqual(before.get(key), hashlib.sha256(original).hexdigest())
        self.assertNotEqual(before.get(key), after.get(key))
        self.assertEqual(strict_manifest(self.crate, self.crate, self.root), after)

    def test_explicit_nested_asset_is_hash_bound(self):
        assets = self.root / 'assets'
        asset = assets / 'layout/target/mayhem-header.bin'
        asset.parent.mkdir(parents=True)
        captured = (ROOT / 'evidence/original/mayhem/deployed.so').read_bytes()
        asset.write_bytes(captured[:64])
        key = asset.relative_to(self.root).as_posix()
        before = self.manifest(assets)
        asset.write_bytes(captured[64:128])
        after = self.manifest(assets)
        self.assertNotEqual(captured[:64], asset.read_bytes())
        self.assertNotEqual(before, after)
        self.assertEqual(before.get(key), hashlib.sha256(captured[:64]).hexdigest())
        self.assertNotEqual(before.get(key), after.get(key))
        self.assertEqual(strict_manifest(self.crate, self.crate, self.root, [assets]), after)

    def test_root_build_directory_and_git_metadata_stay_excluded(self):
        for name in ('target/build/generated.rs', 'src/.git/metadata.rs'):
            generated = self.crate / name
            generated.parent.mkdir(parents=True)
            generated.write_text('not a source input\n', encoding='utf-8')
        keys = self.manifest()
        self.assertNotIn('crates/native-transfer-fee/target/build/generated.rs', keys)
        self.assertNotIn('crates/native-transfer-fee/src/.git/metadata.rs', keys)
        self.assertIn('crates/native-transfer-fee/src/lib.rs', keys)
        self.assertIn('crates/native-transfer-fee/Cargo.toml', keys)


if __name__ == '__main__':
    unittest.main()
