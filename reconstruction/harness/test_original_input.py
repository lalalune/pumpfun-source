"""Exercise the Git placeholder against the complete retained Pump capture."""
import gzip
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import score
from original_input import copy_original_inputs, resolve_original


REPO = Path(__file__).resolve().parents[2]
CAPTURE = REPO / 'evidence/original/pump/deployed.so'
LINK = b'../../evidence/original/pump/deployed.so'


class OriginalInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.base = self.root / 'reconstruction/base'
        self.base.mkdir(parents=True)
        self.target = self.root / 'evidence/original/pump/deployed.so'
        self.target.parent.mkdir(parents=True)
        shutil.copyfile(CAPTURE, self.target)
        self.original = self.base / 'original.so'
        self.original.write_bytes(LINK)
        shutil.copyfile(REPO / 'reconstruction/base/functions.tsv', self.base / 'functions.tsv')

    def test_exact_git_payload_resolves_to_complete_retained_elf(self):
        self.assertEqual(resolve_original(self.original), self.target.resolve())
        self.assertEqual(self.original.read_bytes(), LINK)
        self.assertEqual(hashlib.sha256(resolve_original(self.original).read_bytes()).hexdigest(),
                         '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d')

    def test_arbitrary_text_is_not_followed(self):
        for payload in (LINK + b'\n', LINK.replace(b'pump', b'fees'), b'../elsewhere.so'):
            with self.subTest(payload=payload):
                self.original.write_bytes(payload)
                self.assertEqual(resolve_original(self.original), self.original)

    def test_missing_fixed_target_is_explicit(self):
        self.target.unlink()
        with self.assertRaisesRegex(FileNotFoundError, 'captured original symlink target missing'):
            resolve_original(self.original)

    def test_direct_elf_and_native_symlink_keep_existing_behavior(self):
        self.assertEqual(resolve_original(self.target), self.target)
        link = self.base / 'native.so'
        try:
            link.symlink_to(self.target)
        except OSError as error:
            self.skipTest(f'OS does not permit native symlink creation: {error}')
        self.assertEqual(resolve_original(link), link)
        self.assertEqual(resolve_original(link).read_bytes(), CAPTURE.read_bytes())

    def test_relocated_snapshot_scores_identical_1035_windows(self):
        snapshot = self.root / 'isolated-snapshot'
        snapshot.mkdir()
        copy_original_inputs(self.base, snapshot)
        self.assertEqual((snapshot / 'original.so').read_bytes(), CAPTURE.read_bytes())
        with patch.object(score, 'BASE', self.base):
            placeholder_windows = score.original_windows()
        with patch.object(score, 'BASE', snapshot):
            direct_windows = score.original_windows()
        self.assertEqual(placeholder_windows, direct_windows)
        self.assertEqual(len(direct_windows), 1035)
        self.assertEqual(sum(row['bytes'] for row in direct_windows), 1792208)
        for field, expected in (
            ('raw', '37cc788bba53d0d90446ea0795463dae60713f14af11902bccd678281f36ec6a'),
            ('norm', '048af8f1ce897cb8528f721680903b35af2685cfdc0a7811414344b20c2d9f48'),
        ):
            self.assertEqual(hashlib.sha256(b''.join(w[field] for w in direct_windows)).hexdigest(), expected)

    def test_retained_candidate_memberships_are_identical(self):
        archive = REPO / 'reconstruction/pump-main/lanes/v3-sell-payment-layout/candidate.so.gz'
        candidate = self.root / 'candidate.so'
        candidate.write_bytes(gzip.decompress(archive.read_bytes()))
        self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(),
                         '969811b0e0f673b693695ea651008cacd93eafa5a663dd8bec0e61d3b22d09a9')
        with patch.object(score, 'BASE', self.base):
            linked = score.score_with_hash(candidate)
        shutil.copyfile(CAPTURE, self.original)
        with patch.object(score, 'BASE', self.base):
            direct = score.score_with_hash(candidate)
        self.assertEqual(linked, direct)
        self.assertEqual(len(direct[0]), 1035)


if __name__ == '__main__':
    unittest.main()
