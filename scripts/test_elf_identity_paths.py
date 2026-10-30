"""Analysis identities use repository-relative POSIX paths on every host."""
import hashlib
from pathlib import PurePosixPath,PureWindowsPath
from unittest.mock import patch
import unittest
import window_elf_reader as reader
class IdentityPathTests(unittest.TestCase):
 def item(self,path):
  item=reader.Elf.__new__(reader.Elf);item.path=path;item.b=b'header text footer';item.lo=7;item.hi=11
  return item
 def test_windows_paths_are_portable_manifest_keys(self):
  with patch.object(reader,'REPO',PureWindowsPath('C:/repo')):
   result=self.item(PureWindowsPath('C:/repo/artifacts/nested/candidate.so')).identity()
  self.assertEqual(result['path'],'artifacts/nested/candidate.so')
  self.assertEqual(result['sha256'],hashlib.sha256(b'header text footer').hexdigest())
  self.assertEqual(result['text_sha256'],hashlib.sha256(b'text').hexdigest())
 def test_posix_paths_and_outside_repository_rejection_are_unchanged(self):
  with patch.object(reader,'REPO',PurePosixPath('/repo')):
   self.assertEqual(self.item(PurePosixPath('/repo/a.so')).identity()['path'],'a.so')
   with self.assertRaises(ValueError):self.item(PurePosixPath('/outside/a.so')).identity()
if __name__=='__main__':unittest.main()
