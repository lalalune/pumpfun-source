import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import source_inputs


class SourceScanErrorTests(unittest.TestCase):
    def test_root_disappearing_at_scan_boundary_does_not_produce_an_empty_receipt(self):
        with tempfile.TemporaryDirectory(prefix='source-scan-') as temporary:
            owned = Path(temporary).resolve()
            self.assertEqual(owned.parent,Path(tempfile.gettempdir()).resolve())
            source = owned/'source';source.mkdir()
            real_scan = os.scandir
            def scan(path):
                if Path(path) == source:
                    source.rmdir()
                return real_scan(path)
            with patch.object(source_inputs.os,'scandir',side_effect=scan):
                with self.assertRaises(FileNotFoundError): source_inputs.snapshot(source)
            self.assertFalse(source.exists())

    def test_failed_child_directory_scan_cannot_return_a_partial_receipt(self):
        with tempfile.TemporaryDirectory(prefix='source-scan-') as temporary:
            owned = Path(temporary).resolve()
            source = owned/'source';source.mkdir()
            nested = source/'nested';nested.mkdir()
            marker = nested/'lost.rs';marker.write_bytes(b'pub fn temporary() {}')
            (source/'lib.rs').write_bytes(b'pub fn retained() {}')
            real_scan = os.scandir
            def scan(path):
                if Path(path) == nested:
                    marker.unlink();nested.rmdir()
                return real_scan(path)
            with patch.object(source_inputs.os,'scandir',side_effect=scan):
                with self.assertRaises(FileNotFoundError): source_inputs.snapshot(source)
            self.assertEqual((source/'lib.rs').read_bytes(),b'pub fn retained() {}')

    def test_existing_empty_and_nested_sources_still_snapshot_normally(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            self.assertEqual(source_inputs.snapshot(source)['files'],[])
            nested = source/'nested';nested.mkdir()
            (nested/'lib.rs').write_bytes(b'pub fn present() {}')
            result = source_inputs.snapshot(source)
            self.assertEqual([row['path'] for row in result['files']],['nested/lib.rs'])
            self.assertEqual(source_inputs.snapshot(source),result)


if __name__ == '__main__': unittest.main()
