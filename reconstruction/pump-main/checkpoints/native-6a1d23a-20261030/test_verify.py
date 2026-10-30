"""Offline checkpoint rejection controls; no SDK, compiler or service required."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify as v


class CheckpointTests(unittest.TestCase):
    def test_git_proof_checks_real_commit_and_source_leaf_set(self):
        proof = v.GitProof(v.q.read_json(HERE / 'git-proof.json'))
        self.assertEqual(len(proof.leaves(v.BASE, 'programs/pump')), 99)
        self.assertEqual(proof.lookup(v.CONTROLLER, v.RUNNER)[1], 'ee6c2af0eab66840b950e9f90479539eef88f3de')

    def test_changed_git_object_rejected(self):
        proof = v.q.read_json(HERE / 'git-proof.json')
        proof['objects'][v.BASE]['base64'] = 'eA=='
        with self.assertRaisesRegex(ValueError, 'Git object hash'): v.GitProof(proof)

    def test_changed_source_binding_rejected(self):
        proof = v.q.read_json(HERE / 'git-proof.json')
        first = next(iter(proof['bindings'][v.BASE].values()))
        first['gitBlob'] = '0' * 40
        with self.assertRaisesRegex(ValueError, 'Git leaf'): v.GitProof(proof)

    def test_archive_paths_fail_closed(self):
        for path in ('../outside','/absolute','a/../b','a\\b','a//b',''):
            with self.subTest(path=path), self.assertRaises(ValueError): v.safe_name(path)

    def test_native_archive_corruption_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp); archive = tmp / 'broken.zip'; archive.write_bytes(b'not the hosted archive')
            with self.assertRaisesRegex(ValueError, 'archive SHA256'):
                v.unpack_zip(archive, tmp, {})
            self.assertEqual(sorted(p.name for p in tmp.iterdir()), ['broken.zip'])

    def test_explicit_registry_missing_or_changed_never_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for value in (None, b'changed'):
                if value is not None: (tmp/'entry').write_bytes(value)
                with self.assertRaisesRegex(ValueError, 'local input absent/different'):
                    v.local_map(tmp, {'entry': v.q.sha(b'expected')})

    def test_local_sdk_cannot_pass_from_an_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'SDK file/symlink set'):
                v.sdk_check(Path(tmp), {'entries': {'rust/bin/rustc': {}}})

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'receipt.json'; output.write_bytes(b'prior receipt')
            result = subprocess.run([sys.executable, '-I', '-B', str(HERE/'verify.py'),
                '--original', str(Path(tmp)/'not-needed'), '--report', str(output)],
                capture_output=True, env={**os.environ, 'PATH':''})
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'report output already exists',result.stderr)
            self.assertEqual(output.read_bytes(), b'prior receipt')


if __name__ == '__main__': unittest.main()
