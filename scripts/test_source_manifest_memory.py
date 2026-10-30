"""Explicit large compiler inputs must not be copied wholesale while hashing."""
import hashlib
from pathlib import Path
import tempfile
import tracemalloc
import unittest
from build_source_manifest import source_manifest
class ManifestMemoryTests(unittest.TestCase):
 def test_large_explicit_input_hash_is_exact_with_bounded_python_memory(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);crate=root/'crate';crate.mkdir();(crate/'Cargo.toml').write_text('[package]\nname="synthetic"\n',encoding='utf-8')
   asset=root/'large-input.bin';chunk=b'synthetic-input\0'*4096;digest=hashlib.sha256()
   with asset.open('wb') as output:
    for _ in range(256):output.write(chunk);digest.update(chunk)
   tracemalloc.start()
   try:
    manifest=source_manifest(crate,root,root,[asset]);peak=tracemalloc.get_traced_memory()[1]
   finally:tracemalloc.stop()
   self.assertEqual(manifest['large-input.bin'],digest.hexdigest())
   self.assertLess(peak,2*1024*1024,f'peak={peak}, input={asset.stat().st_size}')
if __name__=='__main__':unittest.main()
