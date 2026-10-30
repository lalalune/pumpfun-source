"""A packet manifest that is itself a link must not revalidate as a pass.

check_manifest link-checks every file the manifest declares, but the
manifest is also an input: a symlinked manifest can point outside the
packet and declare only a subset of its files, leaving the rest unhashed.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import revalidate_all as rv  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class RevalidateManifestLinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.packet = self.root / 'packet'
        self.packet.mkdir()
        (self.packet / 'data.txt').write_bytes(b'declared bytes\n')
        (self.packet / 'undeclared.txt').write_bytes(b'never hashed\n')
        # A manifest declaring only data.txt: subset declaration is the
        # frozen checker's accepted behavior for a regular manifest.
        self.subset = json.dumps({'data.txt': sha256(b'declared bytes\n')})

    def test_regular_subset_manifest_passes(self):
        (self.packet / 'manifest.json').write_text(self.subset)
        result = rv.check_manifest(self.packet)
        self.assertEqual(result['status'], 'pass', result)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO control')
    def test_fifo_manifest_is_rejected_without_reading(self):
        os.mkfifo(self.packet / 'manifest.json')
        command = [sys.executable, '-B', '-c',
            'import sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); '
            'import revalidate_all as r; print(r.check_manifest(Path(sys.argv[2])))',
            str(REPO / 'scripts'), str(self.packet)]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('not_a_file', completed.stdout)

    def test_symlinked_manifest_is_rejected(self):
        external = self.root / 'external-manifest.json'
        external.write_text(self.subset)
        (self.packet / 'manifest.json').symlink_to(external)
        result = rv.check_manifest(self.packet)
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(
            any(error.startswith('linked_path') for error in result['errors']),
            result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
