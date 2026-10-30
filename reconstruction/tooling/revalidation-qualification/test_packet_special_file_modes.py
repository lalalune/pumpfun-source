import os
from pathlib import Path
import socket
import stat
import tempfile
import unittest
import audit

@unittest.skipUnless(os.name == 'posix' and hasattr(os, 'mkfifo') and hasattr(socket, 'AF_UNIX'),
                     'requires POSIX FIFOs and Unix-domain sockets')
class PacketSpecialFileModeTests(unittest.TestCase):
    def test_permission_change_invalidates_packet_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            fifo = packet / 'pipe'
            os.mkfifo(fifo)
            sock = packet / 'sock'
            server = socket.socket(socket.AF_UNIX)
            server.bind(str(sock))
            try:
                original_fifo = fifo.stat().st_mode
                original_sock = sock.stat().st_mode
                before = audit.packet_snapshot(packet)
                try:
                    fifo.chmod(stat.S_IMODE(original_fifo) ^ stat.S_IWUSR)
                    sock.chmod(stat.S_IMODE(original_sock) ^ stat.S_IWUSR)
                    self.assertNotEqual(stat.S_IMODE(fifo.stat().st_mode), stat.S_IMODE(original_fifo))
                    self.assertNotEqual(stat.S_IMODE(sock.stat().st_mode), stat.S_IMODE(original_sock))
                    after = audit.packet_snapshot(packet)
                    self.assertNotEqual(before['identity_sha256'], after['identity_sha256'])
                    self.assertEqual(audit.changed_paths(before, after), ['pipe', 'sock'])
                finally:
                    fifo.chmod(original_fifo)
                    sock.chmod(original_sock)
            finally:
                server.close()

    def test_unchanged_permissions_preserve_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            os.mkfifo(packet / 'pipe')
            server = socket.socket(socket.AF_UNIX)
            server.bind(str(packet / 'sock'))
            try:
                first = audit.packet_snapshot(packet)
                second = audit.packet_snapshot(packet)
                self.assertEqual(first, second)
                self.assertEqual(audit.changed_paths(first, second), [])
            finally:
                server.close()
