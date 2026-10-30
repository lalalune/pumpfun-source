"""Rejected workspace layouts must not change the source they protect."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import fastbuild
from source_inputs import snapshot


class SourcePreflightTests(unittest.TestCase):
    def exercise(self, layout, cli=False):
        with tempfile.TemporaryDirectory(prefix='source-preflight-') as temporary:
            root = Path(temporary)
            source = root / 'source'
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
            (source / 'Cargo.lock').write_text('version=3\n')
            (source / 'src/lib.rs').write_text('pub fn preserved() {}\n')
            if layout == 'same':
                work = source
            elif layout == 'nested':
                work = source / 'new-workspace'
            elif layout == 'ancestor':
                work = root
            else:
                work = root / 'alias'
                work.symlink_to(source, target_is_directory=True)
            output = root / 'output'
            before = snapshot(source)
            paths = sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))
            if cli:
                run = subprocess.run([sys.executable, str(Path(fastbuild.__file__)), '--src', str(source),
                                      '--work', str(work), '--out', str(output)], capture_output=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'source must not overlap', run.stderr)
            else:
                with self.assertRaisesRegex(ValueError, 'source must not overlap'):
                    fastbuild.build(source, work, output)
            self.assertEqual(snapshot(source), before, 'rejected build mutated its source receipt')
            self.assertEqual(sorted(p.relative_to(root).as_posix() for p in root.rglob('*')), paths,
                             'rejected build created a workspace directory or lock')

    def test_source_cannot_be_its_own_workspace(self):
        self.exercise('same')

    def test_nested_workspace_does_not_get_created(self):
        self.exercise('nested')

    def test_ancestor_workspace_does_not_get_a_lock(self):
        self.exercise('ancestor')

    def test_symlink_alias_does_not_mutate_source(self):
        self.exercise('alias')

    def test_actual_cli_leaves_rejected_source_unchanged(self):
        self.exercise('same', cli=True)

    @unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
    def test_valid_disjoint_paths_still_build_with_real_sbf_tools(self):
        sdk = Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve()
        with tempfile.TemporaryDirectory(prefix='source-preflight-valid-') as temporary:
            root = Path(temporary)
            source, work, output = (root / name for name in ('source', 'work', 'output'))
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text(
                '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
                '[lib]\ncrate-type=["cdylib"]\n'
                '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
            (source / 'Cargo.lock').write_text(
                'version=3\n[[package]]\nname="pump-recovered"\nversion="0.1.0"\n')
            (source / 'src/lib.rs').write_text(
                '#![no_std]\n#[no_mangle] pub extern "C" fn entrypoint(_: *mut u8)->u64 { 0 }\n'
                '#[panic_handler] fn panic(_: &core::panic::PanicInfo)->! { loop {} }\n')
            before = snapshot(source)
            recipe = {'triple': 'sbf-solana-solana', 'rustc': sdk / 'rust/bin/rustc',
                      'template': root / 'no-template'}
            with patch.object(fastbuild, 'SDK', sdk), \
                 patch.dict(fastbuild.RECIPES, {'identity': recipe}), \
                 patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                 patch.object(Path, 'home', return_value=root / 'home'):
                result = fastbuild.build(source, work, output, quiet=True, recipe='identity')
            self.assertTrue(result['ok'])
            self.assertTrue((output / 'unstripped.so').read_bytes().startswith(b'\x7fELF'))
            self.assertEqual(snapshot(source), before)


if __name__ == '__main__':
    unittest.main()
