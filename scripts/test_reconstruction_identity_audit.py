"""Guard exact-byte audit against allocation masking and silent stale fallback."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


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

    def write_snapshot(self, root):
        (root / 'original.so').write_bytes(self.raw)
        changed = bytearray(self.raw)
        text = next(s for s in elf_layout(self.raw)['sections'] if s['name'] == '.text')
        changed[text['offset'] + 1] ^= 1
        (root / 'candidate.so').write_bytes(changed)
        index = {'programs': {'selected': {
            'original_path': 'original.so', 'candidate_path': 'candidate.so',
            'original_sha256': hashlib.sha256(self.raw).hexdigest(),
            'candidate_sha256': hashlib.sha256(changed).hexdigest(),
        }}}
        (root / 'index.json').write_text(json.dumps(index))
        return index

    def test_cli_audits_explicit_snapshot_when_current_status_file_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_snapshot(root)
            output = root / 'audit.json'
            process = subprocess.run([
                sys.executable, '-B', str(ROOT / 'scripts/reconstruction_identity_audit.py'),
                '--repo', str(root), '--index', 'index.json', '--output', str(output),
            ], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(output.read_text())
            missing = {'path': 'repro/status.json', 'exists': False}
            self.assertEqual(result['current_status_file'], missing)
            self.assertEqual(json.loads(process.stdout)['current_status_file'], missing)
            self.assertEqual(result['current_status_health'], {})
            self.assertEqual(set(result['input_sha256']), {'index.json', 'original.so', 'candidate.so'})
            selected = result['snapshot_programs']['selected']
            self.assertEqual(selected['candidate_path'], 'candidate.so')
            self.assertFalse(selected['allocation_comparison']['full_byte_equality'])
            self.assertEqual(selected['allocation_comparison']['different_positions_in_shared_length'], 1)
            self.assertFalse(selected['source_completeness_inferred'])
            self.assertFalse(selected['historical_compiler_identity_proven'])

    def test_empty_current_status_is_distinct_from_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'repro').mkdir()
            (root / 'repro/status.json').write_text('{}')
            (root / 'index.json').write_text('{"programs": {}}')
            result = audit(root, 'index.json')
            self.assertEqual(result['current_status_file'], {'path': 'repro/status.json', 'exists': True})
            self.assertIn('repro/status.json', result['input_sha256'])

    def test_malformed_current_status_is_not_treated_as_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'repro').mkdir()
            (root / 'index.json').write_text('{"programs": {}}')
            for contents in ('{', 'null', '[]'):
                with self.subTest(contents=contents):
                    (root / 'repro/status.json').write_text(contents)
                    with self.assertRaises((json.JSONDecodeError, AttributeError)):
                        audit(root, 'index.json')

    def test_missing_status_does_not_bypass_snapshot_hash_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_snapshot(root)
            (root / 'candidate.so').write_bytes(self.raw)
            with self.assertRaises(ValueError):
                audit(root, 'index.json')

    def test_missing_status_does_not_select_a_historical_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_snapshot(root)
            (root / 'candidate.so').rename(root / 'historical.so')
            result = audit(root, 'index.json')
            self.assertEqual(result['snapshot_programs']['selected'], {
                'error': 'snapshot_candidate_missing', 'candidate_path': 'candidate.so',
            })
            self.assertNotIn('historical.so', result['input_sha256'])


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
