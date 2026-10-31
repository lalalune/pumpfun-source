"""Publishing a report must flush the directory entry, not only the bytes.

fsync on the staging file makes its contents durable, but the rename or hard
link that publishes it is a directory update. Without a second fsync a crash
after write() returned can leave the previous report visible, so the caller
that observed success and the report on disk disagree.
"""
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


if __name__ == '__main__':
    unittest.main()
