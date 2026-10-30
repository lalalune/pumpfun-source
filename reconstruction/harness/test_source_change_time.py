import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from source_inputs import snapshot


class SourceChangeTimeTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='nt','Windows st_ctime creation-time semantics')
    def test_same_size_write_with_restored_mtime_cannot_certify_a_mixed_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            asset = source/'asset.bin'
            first,second = b'A'*(2<<20),b'B'*(2<<20)
            asset.write_bytes(first)
            before = asset.stat()
            identity = lambda value:(value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
            real_open = Path.open
            modified = False
            class Reader:
                def __init__(self,stream):self.stream=stream
                def __enter__(self):self.stream.__enter__();return self
                def __exit__(self,*args):return self.stream.__exit__(*args)
                def fileno(self):return self.stream.fileno()
                def read(self,size):
                    nonlocal modified
                    data = self.stream.read(size)
                    if data and not modified:
                        modified = True
                        asset.write_bytes(second)
                        os.utime(asset,ns=(before.st_atime_ns,before.st_mtime_ns))
                        self_test.assertEqual(identity(asset.stat()),identity(before))
                    return data
            self_test = self
            def open_path(path,mode='r',*args,**kwargs):
                stream=real_open(path,mode,*args,**kwargs)
                return Reader(stream) if path==asset and mode=='rb' else stream
            with patch.object(Path,'open',open_path):
                with self.assertRaisesRegex(ValueError,'changed while hashing'):
                    snapshot(source)
            self.assertTrue(modified)
            self.assertEqual(asset.read_bytes(),second)

    def test_unchanged_multichunk_source_retains_its_exact_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)
            payload=b'unchanged asset'*(1<<18)
            (source/'asset.bin').write_bytes(payload)
            first=snapshot(source)
            self.assertEqual(first['files'][0]['sha256'],hashlib.sha256(payload).hexdigest())
            self.assertEqual(snapshot(source),first)


if __name__=='__main__':unittest.main()
