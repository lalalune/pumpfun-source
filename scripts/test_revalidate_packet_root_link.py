"""A packet directory that is itself a link must not revalidate as a pass.

manifest_file's linked-ancestry walk stops at packet_dir without ever
lstat-ing it, so a packet rooted in an external tree passes the frozen
checker (and its external verify.py becomes the packet's verdict). The
successor adapter already rejects linked packet roots; the frozen
checker must too.
"""

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import revalidate_all as rv  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class RevalidatePacketRootLinkTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        # An internally consistent packet living outside the packet tree.
        self.external = self.root / 'external-packet'
        self.external.mkdir()
        (self.external / 'data.txt').write_bytes(b'outside bytes\n')
        (self.external / 'manifest.json').write_text(json.dumps(
            {'data.txt': sha256(b'outside bytes\n')}))

    def test_real_packet_directory_passes(self):
        result = rv.check_manifest(self.external)
        self.assertEqual(result['status'], 'pass', result)

    def test_symlinked_packet_directory_is_rejected(self):
        link = self.root / 'packet-link'
        link.symlink_to(self.external, target_is_directory=True)
        result = rv.check_manifest(link)
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(
            any(error.startswith('linked_path') for error in result['errors']),
            result)

    def test_symlinked_subdirectory_still_rejected(self):
        packet = self.root / 'packet'
        packet.mkdir()
        (packet / 'alias').symlink_to(self.external, target_is_directory=True)
        (packet / 'manifest.json').write_text(json.dumps(
            {'alias/data.txt': sha256(b'outside bytes\n')}))
        result = rv.check_manifest(packet)
        self.assertEqual(result['status'], 'fail', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
