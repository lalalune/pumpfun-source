import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import deep_disassembly as packets


class UnsupportedExchange(unittest.TestCase):
    def test_unsupported_hosts_fail_before_native_library_loading(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, destination = root / 'staging', root / 'packet'
            source.mkdir(); destination.mkdir()
            (source / 'new').write_bytes(b'new')
            (destination / 'prior').write_bytes(b'prior')
            for platform, name in (('win32', 'nt'), ('freebsd13', 'posix')):
                with self.subTest(platform=platform):
                    with patch.object(packets.sys, 'platform', platform), patch.object(packets.os, 'name', name):
                        with patch.object(packets.ctypes, 'CDLL') as library:
                            with self.assertRaises(OSError) as error:
                                packets.rename_directory(source, destination, exchange=True)
                            self.assertEqual(error.exception.errno, errno.ENOTSUP)
                            library.assert_not_called()
                    self.assertEqual((source / 'new').read_bytes(), b'new')
                    self.assertEqual((destination / 'prior').read_bytes(), b'prior')

    @unittest.skipUnless(packets.os.name == 'nt', 'real Windows no-replace rename')
    def test_windows_initial_publication_still_works(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, destination = root / 'staging', root / 'packet'
            source.mkdir()
            (source / 'new').write_bytes(b'new')
            packets.rename_directory(source, destination)
            self.assertFalse(source.exists())
            self.assertEqual((destination / 'new').read_bytes(), b'new')
            source.mkdir()
            (source / 'next').write_bytes(b'next')
            with self.assertRaises(OSError) as error:
                packets.rename_directory(source, destination, exchange=True)
            self.assertEqual(error.exception.errno, errno.ENOTSUP)
            self.assertEqual((destination / 'new').read_bytes(), b'new')
            self.assertEqual((source / 'next').read_bytes(), b'next')


if __name__ == '__main__': unittest.main()
