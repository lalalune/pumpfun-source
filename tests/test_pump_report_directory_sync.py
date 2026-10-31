"""Publishing a report must flush the directory entry, not only the bytes.

fsync on the staging file makes its contents durable, but the rename or hard
link that publishes it is a directory update. Without a second fsync a crash
after write() returned can leave the previous report visible, so the caller
that observed success and the report on disk disagree.
"""
import errno
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_differential_output as publication


class DirectorySyncTests(unittest.TestCase):
    def write_recording_syncs(self, publisher, payload):
        """Run write() and report, in order, whether each fsync targeted a directory."""
        real_fsync = os.fsync
        directories = []

        def record(descriptor):
            directories.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
            real_fsync(descriptor)

        with mock.patch.object(publication.os, 'fsync', side_effect=record):
            publisher.write(payload)
        return directories

    def test_write_flushes_the_directory_that_publishes_the_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            publisher = publication.PumpReport(root / 'out' / 'report.json', root, None, __file__)
            synced = self.write_recording_syncs(publisher, b'{"cases": []}')
            self.assertEqual((root / 'out' / 'report.json').read_bytes(), b'{"cases": []}')
            self.assertEqual(synced, [False, True], 'staged bytes and the report directory are both flushed')

    def test_replacement_flushes_the_directory_after_the_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'out' / 'report.json'
            output.parent.mkdir()
            output.write_bytes(b'{"cases": ["stale"]}')
            publisher = publication.PumpReport(output, root, None, __file__)
            synced = self.write_recording_syncs(publisher, b'{"cases": ["fresh"]}')
            self.assertEqual(output.read_bytes(), b'{"cases": ["fresh"]}')
            self.assertEqual(synced, [False, True])

    def test_a_rejected_output_does_not_flush_the_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'out' / 'report.json'
            publisher = publication.PumpReport(output, root, None, __file__, overwrite=False)
            output.write_bytes(b'{"cases": ["kept"]}')
            with self.assertRaises(FileExistsError):
                self.write_recording_syncs(publisher, b'{"cases": ["lost"]}')
            self.assertEqual(output.read_bytes(), b'{"cases": ["kept"]}')

    def test_fresh_only_publication_flushes_bytes_then_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            publisher = publication.PumpReport(root / 'report.json', root, None, __file__, overwrite=False)
            self.assertEqual(self.write_recording_syncs(publisher, b'complete'), [False, True])

    @unittest.skipIf(os.name == 'nt', 'directory descriptors are not supported on Windows')
    def test_directory_io_failure_is_reported_after_complete_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'report.json'
            publisher = publication.PumpReport(output, root, None, __file__)
            real_sync = os.fsync
            def failing(descriptor):
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise OSError(errno.EIO, 'controlled directory I/O failure')
                return real_sync(descriptor)
            with mock.patch.object(publication.os, 'fsync', side_effect=failing):
                with self.assertRaisesRegex(OSError, 'controlled directory I/O failure'):
                    publisher.write(b'complete')
            self.assertEqual(output.read_bytes(), b'complete')
            self.assertEqual(list(root.glob('.report.json.*')), [])

    @unittest.skipIf(os.name == 'nt', 'directory descriptors are not supported on Windows')
    def test_unsupported_directory_sync_preserves_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'report.json'
            publisher = publication.PumpReport(output, root, None, __file__)
            real_sync = os.fsync
            def unsupported(descriptor):
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    raise OSError(errno.ENOTSUP, 'directory sync unsupported')
                return real_sync(descriptor)
            with mock.patch.object(publication.os, 'fsync', side_effect=unsupported):
                publisher.write(b'complete')
            self.assertEqual(output.read_bytes(), b'complete')

    @unittest.skipIf(os.name == 'nt', 'fresh publication uses rename on Windows')
    def test_fresh_publication_preserves_a_recreated_staging_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'report.json'
            publisher = publication.PumpReport(output, root, None, __file__, overwrite=False)
            real_sync = os.fsync
            replacements = []
            def replace_stage(descriptor):
                if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                    stage = next(root.glob('.report.json.*'))
                    stage.unlink()
                    stage.write_bytes(b'new staging owner')
                    replacements.append(stage)
                return real_sync(descriptor)
            with mock.patch.object(publication.os, 'fsync', side_effect=replace_stage):
                publisher.write(b'complete receipt')
            self.assertEqual(output.read_bytes(), b'complete receipt')
            self.assertEqual(replacements[0].read_bytes(), b'new staging owner')

    @unittest.skipIf(os.name == 'nt', 'fresh publication uses rename on Windows')
    def test_disappearing_owned_stage_does_not_fail_complete_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / 'report.json'
            publisher = publication.PumpReport(output, root, None, __file__, overwrite=False)
            real_lstat, real_unlink = Path.lstat, Path.unlink
            removed = []
            def lstat_then_remove(path, *args, **kwargs):
                metadata = real_lstat(path, *args, **kwargs)
                if path.name.startswith('.report.json.') and output.exists():
                    real_unlink(path)
                    removed.append(path)
                return metadata
            with mock.patch.object(Path, 'lstat', lstat_then_remove):
                publisher.write(b'complete receipt')
            self.assertEqual(len(removed), 1)
            self.assertEqual(output.read_bytes(), b'complete receipt')


if __name__ == '__main__':
    unittest.main()
