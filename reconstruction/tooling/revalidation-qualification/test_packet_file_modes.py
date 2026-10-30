import os
from pathlib import Path
import stat
import tempfile
import unittest
import audit

class PacketModeTests(unittest.TestCase):
    def test_permission_change_invalidates_packet_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet=Path(temporary);file=packet/'artifact.txt';file.write_bytes(b'retained evidence\n')
            original=file.stat().st_mode
            before=audit.packet_snapshot(packet)
            try:
                file.chmod(stat.S_IREAD)
                self.assertNotEqual(stat.S_IMODE(file.stat().st_mode),stat.S_IMODE(original))
                after=audit.packet_snapshot(packet)
                self.assertNotEqual(before['identity_sha256'],after['identity_sha256'])
                self.assertEqual(audit.changed_paths(before,after),['artifact.txt'])
            finally:file.chmod(original)
    def test_unchanged_permissions_preserve_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet=Path(temporary);(packet/'artifact.txt').write_bytes(b'retained evidence\n')
            first=audit.packet_snapshot(packet);second=audit.packet_snapshot(packet)
            self.assertEqual(first,second)
            self.assertEqual(audit.changed_paths(first,second),[])
