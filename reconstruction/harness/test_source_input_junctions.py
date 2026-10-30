import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from source_inputs import snapshot


class SourceInputJunctionTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Windows directory junction admission')
    def test_junction_to_an_outside_directory_is_not_admitted_as_source(self):
        with tempfile.TemporaryDirectory(prefix='source-junction-') as temporary:
            root = Path(temporary).resolve()
            self.assertEqual(root.parent,Path(tempfile.gettempdir()).resolve())
            source,outside = root/'source',root/'outside'
            source.mkdir();outside.mkdir()
            (source/'lib.rs').write_bytes(b'pub fn local() {}')
            payload = b'pub fn external() {}'
            marker = outside/'external.rs';marker.write_bytes(payload)
            link = source/'linked'
            command = 'New-Item -ItemType Junction -Path $env:HARNESS_TEST_LINK -Target $env:HARNESS_TEST_TARGET -ErrorAction Stop | Out-Null'
            result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],env=dict(os.environ,HARNESS_TEST_LINK=str(link),HARNESS_TEST_TARGET=str(outside)),capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
            self.assertTrue(link.is_junction())
            self.assertFalse(link.is_symlink())
            try:
                with self.assertRaisesRegex(ValueError,'source directory.*links'):
                    snapshot(source)
                self.assertEqual(marker.read_bytes(),payload)
            finally:
                # Remove only the junction entry before the owned temporary tree.
                link.rmdir()
            self.assertEqual(marker.read_bytes(),payload)

    def test_real_nested_directories_keep_their_exact_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            nested = source/'nested';nested.mkdir()
            payload = b'pub fn real() {}'
            (nested/'lib.rs').write_bytes(payload)
            receipt = snapshot(source)
            self.assertEqual([row['path'] for row in receipt['files']],['nested/lib.rs'])
            self.assertEqual(receipt['files'][0]['sha256'],hashlib.sha256(payload).hexdigest())
            self.assertEqual(snapshot(source),receipt)


if __name__ == '__main__': unittest.main()
