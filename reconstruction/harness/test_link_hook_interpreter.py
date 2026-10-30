"""Use the selected Python even when PATH has an older Python or no python3."""
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import fastbuild
from source_inputs import snapshot


@unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
class LinkInterpreterTests(unittest.TestCase):
    def test_real_link_uses_current_interpreter_independently_of_path(self):
        sdk = Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve()
        with tempfile.TemporaryDirectory(prefix='pump-link-python-') as temporary:
            root = Path(temporary)
            source, work, output = (root / n for n in ('source', 'work', 'output'))
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
            (source / 'link').mkdir()
            shutil.copy2(Path(fastbuild.__file__).with_name('sbf_default.ld'), source / 'link/ordered.ld')
            tools = root / 'tools-without-python'
            tools.mkdir()
            (tools / 'rsync').symlink_to(shutil.which('rsync'))
            paths = {'selected-python': str(Path(sys.executable).parent) + os.pathsep + os.defpath,
                     'system-python': os.defpath, 'no-python': str(tools)}
            recipe = {'triple': 'sbf-solana-solana', 'rustc': sdk / 'rust/bin/rustc',
                      'template': root / 'no-template'}
            with patch.object(fastbuild, 'SDK', sdk), \
                 patch.dict(fastbuild.RECIPES, {'identity': recipe}), \
                 patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                 patch.object(Path, 'home', return_value=root / 'home'):
                for pinned in (True, False):
                    if not pinned:
                        (source / 'link/ordered.ld').unlink()
                    before, control = snapshot(source), None
                    for label, path in paths.items():
                        with self.subTest(pinned=pinned, path=label), patch.dict(os.environ, {'PATH': path}):
                            result = fastbuild.build(source, work, output, recipe='identity', quiet=True)
                            self.assertTrue(result['ok'], (output / 'build.log').read_text())
                            current = hashlib.sha256((output / 'unstripped.so').read_bytes()).hexdigest()
                            if control is None:
                                control = current
                            else:
                                self.assertEqual(current, control)
                            self.assertEqual((output / 'link-receipt.json').is_file(), pinned)
                            self.assertEqual((output / 'link.map').is_file(), pinned)
                    self.assertEqual(snapshot(source), before)


if __name__ == '__main__':
    unittest.main()
