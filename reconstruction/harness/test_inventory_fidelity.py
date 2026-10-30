import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from treediff import tree_diff, tree_files
from attempt_applicability import classify, FIELDS


class InventoryFidelityTests(unittest.TestCase):
    def test_mode_changes_and_executable_additions_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); base = root/'base'; new = root/'new'; target = root/'checkout/programs/pump'
            for directory in (base, new, target):
                directory.mkdir(parents=True)
                (directory/'helper').write_bytes(b'#!/bin/sh\nexit 0\n')
                (directory/'helper').chmod(0o644)
            (new/'helper').chmod(0o755)
            (new/'new-helper').write_bytes(b'#!/bin/sh\nexit 0\n'); (new/'new-helper').chmod(0o711)
            (new/'empty-helper').touch(); (new/'empty-helper').chmod(0o755)
            subprocess.run(['git','init','-q',str(root/'checkout')],check=True)
            patch = tree_diff(base,new).encode()
            applied = subprocess.run(['git','-C',str(root/'checkout'),'apply','-'],input=patch,capture_output=True)
            self.assertEqual(applied.returncode,0,applied.stderr)
            for name in ['helper','new-helper','empty-helper']:
                self.assertTrue((target/name).stat().st_mode & 0o111,name)
                self.assertEqual((target/name).read_bytes(),(new/name).read_bytes())
            self.assertEqual(tree_diff(new,new),'')
            # Ordinary text hunks remain deterministic.
            (new/'helper').chmod(0o644); (new/'helper').write_bytes(b'#!/bin/sh\nexit 1\n')
            self.assertIn('-exit 0\n+exit 1\n',tree_diff(base,new))

    @unittest.skipUnless(hasattr(os,'mkfifo'),'requires FIFO support')
    def test_fifo_is_rejected_without_reading_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'regular').write_bytes(b'control')
            self.assertEqual(tree_files(root),{'regular':b'control'})
            os.mkfifo(root/'fifo')
            with self.assertRaisesRegex(ValueError,'special'):
                tree_files(root)

    def test_linked_evidence_root_is_unverifiable(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); real=root/'real';real.mkdir();(real/'receipt').write_bytes(b'evidence')
            link=root/'link';link.symlink_to(real,target_is_directory=True)
            context={key:'a'*64 for key in FIELDS}
            row={'data':{'context':context,'evidence':[{'path':'receipt','sha256':hashlib.sha256(b'evidence').hexdigest()}]}}
            self.assertEqual(classify(row,context,real)['applicability'],'compatible')
            self.assertEqual(classify(row,context,link)['applicability'],'unverifiable')


if __name__=='__main__':unittest.main()
