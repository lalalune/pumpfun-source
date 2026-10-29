"""Guard exact-byte audit against allocation masking and silent stale fallback."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from analyze import elf_layout
import reconstruction_identity_audit
from reconstruction_identity_audit import ROOT, audit, measure


class IdentityAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / 'evidence/dependencies/associated_token/deployed.so').read_bytes()

    def test_identical_artifact_does_not_prove_source_recovery(self):
        result = measure(self.raw, self.raw)
        self.assertTrue(result['allocation_comparison']['full_byte_equality'])
        self.assertFalse(result['source_completeness_inferred'])
        self.assertFalse(result['historical_compiler_identity_proven'])

    def test_allocation_tail_remains_part_of_acceptance(self):
        end = elf_layout(self.raw)['elf_extent']
        original = self.raw[:end] + bytes(16)
        result = measure(original, self.raw[:end])
        self.assertTrue(result['raw_elf_comparison']['full_byte_equality'])
        self.assertFalse(result['allocation_comparison']['full_byte_equality'])
        self.assertEqual(result['allocation_comparison']['length_difference'], -16)

    def test_equal_text_size_cannot_hide_instruction_mutation(self):
        section = next(s for s in elf_layout(self.raw)['sections'] if s['name'] == '.text')
        changed = bytearray(self.raw)
        changed[section['offset'] + 1] ^= 1
        result = measure(self.raw, bytes(changed))
        text = next(s for s in result['sections'] if s['section'] == '.text')
        self.assertEqual(text['original']['size'], text['candidate']['size'])
        self.assertFalse(text['file_payload_comparison']['full_byte_equality'])
        self.assertEqual(text['file_payload_comparison']['different_positions_in_shared_length'], 1)

    def test_missing_current_candidate_is_reported_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'repro').mkdir()
            (root / 'repro/status.json').write_text(json.dumps({'pump': {'candidate_artifact': 'missing.so'}}))
            (root / 'index.json').write_text(json.dumps({'programs': {}}))
            result = audit(root, 'index.json')
            self.assertFalse(result['current_status_health']['pump']['candidate_exists'])
            self.assertNotIn('candidate_sha256', result['current_status_health']['pump'])

    def test_missing_git_binary_degrades_to_null_revision(self):
        # A minimal host without `git` makes check_output raise FileNotFoundError
        # (not CalledProcessError); the read-only audit must still complete.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'repro').mkdir()
            (root / 'repro/status.json').write_text(json.dumps({}))
            (root / 'index.json').write_text(json.dumps({'programs': {}}))
            with mock.patch.object(reconstruction_identity_audit.subprocess, 'check_output',
                                   side_effect=FileNotFoundError(2, 'No such file or directory', 'git')):
                result = audit(root, 'index.json')
            self.assertIsNone(result['repository_revision'])


if __name__ == '__main__':
    unittest.main()
