"""The identity audit must hash the file inside the repository root."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reconstruction_identity_audit as audit


def tree():
    directory = tempfile.TemporaryDirectory()
    root = Path(directory.name)
    (root / 'repro').mkdir()
    (root / 'repro/status.json').write_text(json.dumps({'pump': {}}))
    (root / 'inside.so').write_bytes(b'inside')
    outside = root.parent / 'outside.so'
    outside.write_bytes(b'outside')
    return directory, root, outside


class IdentityAuditPathTests(unittest.TestCase):
    def test_parent_path_and_symlink_are_rejected(self):
        directory, root, outside = tree()
        self.addCleanup(directory.cleanup)
        self.addCleanup(outside.unlink, missing_ok=True)
        index = {
            'programs': {
                'pump': {
                    'original_path': '../outside.so',
                    'original_sha256': '0' * 64,
                    'candidate_path': 'missing.so',
                    'candidate_sha256': '0' * 64,
                }
            }
        }
        (root / 'index.json').write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'escapes root'):
            audit.audit(root, 'index.json')
        os.symlink(outside, root / 'linked.so')
        index['programs']['pump']['original_path'] = 'linked.so'
        (root / 'index.json').write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            audit.audit(root, 'index.json')

    def test_duplicate_json_key_is_rejected(self):
        directory, root, outside = tree()
        self.addCleanup(directory.cleanup)
        self.addCleanup(outside.unlink, missing_ok=True)
        (root / 'index.json').write_text(
            '{"programs": {"pump": {"original_path": "inside.so", "original_path": "linked.so"}}}'
        )
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            audit.audit(root, 'index.json')

    def test_ordinary_missing_candidate_is_reported(self):
        directory, root, outside = tree()
        self.addCleanup(directory.cleanup)
        self.addCleanup(outside.unlink, missing_ok=True)
        digest = __import__('hashlib').sha256(b'inside').hexdigest()
        index = {
            'programs': {
                'pump': {
                    'original_path': 'inside.so',
                    'original_sha256': digest,
                    'candidate_path': 'missing.so',
                    'candidate_sha256': digest,
                }
            }
        }
        (root / 'index.json').write_text(json.dumps(index))
        result = audit.audit(root, 'index.json')
        self.assertEqual(result['snapshot_programs']['pump']['error'], 'snapshot_candidate_missing')


if __name__ == '__main__':
    unittest.main(verbosity=2)
