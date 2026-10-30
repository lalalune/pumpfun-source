"""Downloaded archived673 inputs must be authenticated before publication."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_current673_macos_control as controller


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Current673ArchivePublicationTests(unittest.TestCase):
    def test_hash_failure_does_not_publish_or_leave_temporary_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.bin'
            source.write_bytes(b'untrusted archive bytes')
            destination = root / 'input.tar.bz2'
            with self.assertRaisesRegex(ValueError, 'archive hash mismatch'):
                controller.download_archive(
                    source.as_uri(), '0' * 64, destination)
            self.assertFalse(destination.exists())
            self.assertEqual(list(root.glob('.input.tar.bz2.*')), [])

    def test_authenticated_archive_is_published_at_final_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = b'authenticated archive bytes'
            source = root / 'source.bin'
            source.write_bytes(payload)
            destination = root / 'input.tar.bz2'
            self.assertEqual(
                controller.download_archive(source.as_uri(), sha(payload), destination),
                sha(payload),
            )
            self.assertEqual(destination.read_bytes(), payload)
            self.assertEqual(list(root.glob('.input.tar.bz2.*')), [])

    def test_late_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.bin'
            source.write_bytes(b'authenticated archive')
            destination = root / 'input.tar.bz2'
            copy = controller.shutil.copyfileobj
            def concurrent_writer(src, target):
                copy(src, target)
                destination.write_bytes(b'other retained archive')
            with mock.patch.object(controller.shutil, 'copyfileobj', concurrent_writer):
                with self.assertRaises(FileExistsError):
                    controller.download_archive(source.as_uri(), sha(source.read_bytes()), destination)
            self.assertEqual(destination.read_bytes(), b'other retained archive')
            self.assertEqual(list(root.glob('.input.tar.bz2.*')), [])

    def test_existing_destination_does_not_start_download(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'input.tar.bz2'
            destination.write_bytes(b'existing archive')
            with mock.patch.object(controller.urllib.request, 'urlopen') as download:
                with self.assertRaises(FileExistsError):
                    controller.download_archive('not-contacted', '0' * 64, destination)
                download.assert_not_called()
            self.assertEqual(destination.read_bytes(), b'existing archive')


if __name__ == '__main__':
    unittest.main()
