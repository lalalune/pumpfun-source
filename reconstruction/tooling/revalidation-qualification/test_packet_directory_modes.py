import os
from pathlib import Path
import stat
import tempfile
import unittest
import audit


class PacketDirectoryModeTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_permission_change_invalidates_packet_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            sub = packet / "sub"
            sub.mkdir()
            (sub / "artifact.txt").write_bytes(b"retained evidence\n")
            original = sub.stat().st_mode
            before = audit.packet_snapshot(packet)
            try:
                sub.chmod(stat.S_IREAD | stat.S_IEXEC)
                self.assertNotEqual(
                    stat.S_IMODE(sub.stat().st_mode), stat.S_IMODE(original)
                )
                after = audit.packet_snapshot(packet)
                self.assertNotEqual(
                    before["identity_sha256"], after["identity_sha256"]
                )
                self.assertEqual(audit.changed_paths(before, after), ["sub"])
            finally:
                sub.chmod(original)

    @unittest.skipUnless(os.name == "posix", "POSIX permission semantics")
    def test_unchanged_permissions_preserve_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            sub = packet / "sub"
            sub.mkdir()
            (sub / "artifact.txt").write_bytes(b"retained evidence\n")
            first = audit.packet_snapshot(packet)
            second = audit.packet_snapshot(packet)
            self.assertEqual(first, second)
            self.assertEqual(audit.changed_paths(first, second), [])


if __name__ == "__main__":
    unittest.main()
