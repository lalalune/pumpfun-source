"""Regression controls for symlinked source-manifest inputs."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import tempfile
import unittest

import proof
import sys
sys.path.insert(0, str(proof.REPO / 'scripts'))
import pump_build_verified

P = Path(__file__).resolve().parent


class SourceManifestSymlinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archived = proof._reviewed()
        cls.report = proof.check(proof.REPO)

    def test_real_manifest_is_unchanged(self):
        crate = proof.REPO / 'programs/pump'
        old = self.archived.source_manifest(crate, crate, proof.REPO)
        new = proof.strict_manifest(self.archived, crate, crate, proof.REPO)
        self.assertEqual(old, new)
        self.assertEqual(len(new), 65)
        self.assertEqual(self.report['symlinks'], [])
        self.assertEqual(self.report['files'], 65)

    def test_symlinked_rust_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            crate = root / 'crate'
            (crate / 'src').mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname = "probe"\n')
            outside = root / 'outside.rs'
            outside.write_text('pub fn external() {}\n')
            os.symlink(outside, crate / 'src/lib.rs')
            old = self.archived.source_manifest(crate, crate, root)
            self.assertIn('crate/src/lib.rs', old)
            with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                proof.strict_manifest(self.archived, crate, crate, root)

    def test_symlink_in_extra_input_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            crate = root / 'crate'
            crate.mkdir()
            (crate / 'Cargo.toml').write_text('[package]\nname = "probe"\n')
            assets = root / 'assets'
            assets.mkdir()
            outside = root / 'external.bin'
            outside.write_bytes(b'external')
            os.symlink(outside, assets / 'table.bin')
            old = self.archived.source_manifest(crate, crate, root, [assets])
            self.assertIn('assets/table.bin', old)
            with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                proof.strict_manifest(self.archived, crate, crate, root, [assets])

    def test_outside_path_is_rejected_without_hanging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'root'
            outside = Path(temporary) / 'outside'
            root.mkdir()
            outside.mkdir()
            with self.assertRaisesRegex(ValueError, 'outside repository'):
                proof._plain(outside, root)

    def test_build_verifier_uses_production_guard(self):
        self.assertIs(pump_build_verified.source_manifest, proof.production_strict)

    def test_no_symlink_in_real_programs_pump(self):
        for path in (proof.REPO / 'programs/pump').rglob('*'):
            self.assertFalse(path.is_symlink(), path)

    def saved_observations(self):
        return json.loads(gzip.decompress((P / 'observations.json.gz').read_bytes()))

    def test_saved_claims_match(self):
        self.assertEqual(proof.claims(self.report), proof.claims(self.saved_observations()))

    def test_sealed_source_revision_is_provenance(self):
        saved = self.saved_observations()
        bytes.fromhex(saved['manifest_sha256'])
        changed = dict(saved, manifest_sha256='0' * 64)
        self.assertEqual(proof.claims(changed), proof.claims(self.report))

    def test_claim_drift_is_rejected(self):
        saved = self.saved_observations()
        mutations = {
            'scope': 'a different scope',
            'script': 'scripts/other.py',
            'script_sha256': '0' * 64,
            'program': 'pump_amm',
            'files': saved['files'] + 1,
            'symlinks': ['programs/pump/src/lib.rs'],
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                mutated = dict(saved, **{key: value})
                self.assertNotEqual(proof.claims(mutated), proof.claims(self.report))

    def test_manifest_inventory(self):
        saved = json.loads((P / 'manifest.json').read_text())
        actual = {
            str(path.relative_to(P)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(P.rglob('*'))
            if path.is_file() and path.name != 'manifest.json'
            and '__pycache__' not in path.parts and path.suffix != '.pyc'
        }
        self.assertEqual(saved, actual)


if __name__ == '__main__':
    unittest.main(verbosity=2)
