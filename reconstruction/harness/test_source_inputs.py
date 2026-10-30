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

    def test_real_staged_nested_target_inputs_change_receipt(self):
        (self.source/'Cargo.toml').write_text(
            '[package]\nname="pump-recovered"\nversion="0.1.0"\n'
            '[profile.release]\npanic="abort"\n[workspace]\n')
        (self.source/'Cargo.lock').write_text('version = 3\n')
        (self.source/'src/target').mkdir(parents=True)
        (self.source/'assets/target').mkdir(parents=True)
        (self.source/'src/lib.rs').write_text(
            'pub mod target;\npub static DATA: &[u8] = include_bytes!("../assets/target/data.bin");\n')
        module=self.source/'src/target/mod.rs'
        asset=self.source/'assets/target/data.bin'
        module.write_text('pub const VALUE: u8 = 1;\n')
        asset.write_bytes(b'first\x00')
        before=snapshot(self.source)
        crate=fastbuild.stage(self.source,self.root/'workspace')
        self.assertEqual((crate/'src/target/mod.rs').read_bytes(),module.read_bytes())
        self.assertEqual((crate/'assets/target/data.bin').read_bytes(),asset.read_bytes())
        module.write_text('pub const VALUE: u8 = 2;\n')
        asset.write_bytes(b'other\x00')
        self.assertNotEqual(snapshot(self.source)['sha256'],before['sha256'])
        with self.assertRaisesRegex(ValueError,'assets/target/data.bin|src/target/mod.rs'):
            assert_unchanged(self.source,before)

    def test_nested_target_directory_symlink_is_rejected(self):
        (self.source/'src').mkdir()
        outside=self.root/'external'
        outside.mkdir()
        (outside/'mod.rs').write_text('pub const VALUE: u8 = 1;\n')
        (self.source/'src/target').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'directory symlinks'):
            snapshot(self.source)

    def test_root_target_directory_symlink_is_rejected(self):
        (self.source/'src').mkdir()
        (self.source/'src/lib.rs').write_text(
            '#[path = "../target/mod.rs"] pub mod target;\n')
        outside=self.root/'external'
        outside.mkdir()
        (outside/'mod.rs').write_text('pub const VALUE: u8 = 1;\n')
        (self.source/'target').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'directory symlinks'):
            snapshot(self.source)

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
        (self.root/'crate').mkdir()
        (self.root/'crate/Cargo.toml').write_text('[package]\nname="pump-recovered"\nversion="0.1.0"\n')
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
