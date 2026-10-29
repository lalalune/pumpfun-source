import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import fastbuild
from source_inputs import snapshot, assert_unchanged


class SourceReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'src';self.source.mkdir()
        (self.source/'lib.rs').write_text('fn main() {}\n')

    def test_receipt_is_portable_and_stable_across_root_and_mtime(self):
        import shutil
        other=self.root/'copy';shutil.copytree(self.source,other)
        os.utime(other/'lib.rs',(1,1))
        self.assertEqual(snapshot(self.source),snapshot(other))
        self.assertNotIn(str(self.root),json.dumps(snapshot(self.source)))

    def test_content_names_and_executable_mode_affect_digest(self):
        initial=snapshot(self.source)
        for operation in [lambda:(self.source/'lib.rs').write_text('changed'),
                          lambda:(self.source/'added').write_bytes(b''),
                          lambda:(self.source/'lib.rs').chmod(0o755)]:
            before=snapshot(self.source);operation()
            self.assertNotEqual(before['sha256'],snapshot(self.source)['sha256'])
        with self.assertRaisesRegex(ValueError,'lib.rs'):assert_unchanged(self.source,initial)

    def test_generated_target_and_git_metadata_are_excluded(self):
        before=snapshot(self.source)
        for name in ('target','.git'):
            directory=self.source/name;directory.mkdir();(directory/'generated').write_text('ignored')
        self.assertEqual(snapshot(self.source),before)

    def test_file_and_directory_symlinks_are_rejected(self):
        for target in [self.source/'lib.rs',self.source]:
            link=self.source/'link';link.symlink_to(target)
            try:
                with self.assertRaises(ValueError):snapshot(self.source)
            finally:link.unlink()

    def test_build_rejects_source_mutation_before_compiler(self):
        def stage(source,ws):
            (source/'lib.rs').write_text('mutated while staging');return ws/'crate'
        with patch.object(fastbuild,'stage',side_effect=stage),patch.object(fastbuild,'acquire_slot') as acquire:
            with self.assertRaisesRegex(ValueError,'changed during staging'):
                fastbuild.build(self.source,self.root/'work',self.root/'out')
            acquire.assert_not_called()

    def test_failed_build_retains_receipt_and_digest(self):
        slot=io.StringIO();out=self.root/'out'
        with patch.object(fastbuild,'stage',return_value=self.root/'crate'),patch.object(fastbuild,'acquire_slot',return_value=slot),patch.object(fastbuild.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'compile error')),patch.object(fastbuild,'run_compiler',return_value=(subprocess.CompletedProcess([],1,'compile error'),False),create=True),patch.object(fastbuild,'RECIPES',{'test':{'triple':'test','rustc':self.root/'rustc','template':self.root/'missing'}}):
            result=fastbuild.build(self.source,self.root/'work',out,quiet=True,recipe='test')
        receipt=json.loads((out/'source-inputs.json').read_text())
        self.assertEqual(result['source_sha256'],receipt['sha256']);self.assertFalse(result['ok'])

    def test_source_workspace_overlap_is_rejected_before_staging(self):
        with patch.object(fastbuild,'stage') as stage:
            with self.assertRaisesRegex(ValueError,'overlap'):
                fastbuild.build(self.source,self.source/'work',self.root/'out')
            stage.assert_not_called()


if __name__=='__main__':unittest.main()
