"""Run the inline-capture workflow with real offline Cargo and SBF rustc."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import fastbuild

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'reconstruction/pump-main/lanes/callgraph-census/capture_inline.py'
SPEC = importlib.util.spec_from_file_location('inline_capture_regression', SCRIPT)
capture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture)


@unittest.skipUnless(os.environ.get('PUMP_INLINE_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
class InlineCompilerTests(unittest.TestCase):
    def test_real_compiler_emits_requested_inline_remarks(self):
        sdk = Path(os.environ['PUMP_INLINE_TEST_SDK']).resolve()
        with tempfile.TemporaryDirectory(prefix='pump-inline-compiler-') as temporary:
            root = Path(temporary)
            source = root / 'source'
            (source / 'src').mkdir(parents=True)
            (source / 'Cargo.toml').write_text(
                '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
                '[lib]\ncrate-type=["cdylib"]\n'
                '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
            (source / 'Cargo.lock').write_text(
                'version=3\n[[package]]\nname="pump-recovered"\nversion="0.1.0"\n')
            (source / 'src/lib.rs').write_text(
                '#![no_std]\n'
                '#[inline(never)] fn arithmetic(x:u64)->u64 { x.wrapping_mul(7).wrapping_add(3) }\n'
                '#[no_mangle] pub extern "C" fn entrypoint(input:*const u64)->u64 {\n'
                '    arithmetic(unsafe { core::ptr::read_volatile(input) })\n}\n'
                '#[panic_handler] fn panic(_: &core::panic::PanicInfo)->! { loop {} }\n')
            recipe = {'triple': 'sbf-solana-solana', 'rustc': sdk / 'rust/bin/rustc',
                      'template': root / 'no-template'}
            original_runner = fastbuild.run_compiler
            def run_capture(lines, suffix):
                work, output = root / f'work-{suffix}', root / f'output-{suffix}'
                argv = ['capture_inline.py', '--src', str(source), '--work', str(work),
                        '--out', str(output), '--caller', '.'] + (['--lines'] if lines else [])
                with patch.object(fastbuild, 'SDK', sdk), \
                     patch.dict(fastbuild.RECIPES, {'identity': recipe}), \
                     patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                     patch.object(Path, 'home', return_value=root / 'home'), \
                     patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                    status = capture.main()
                self.assertIs(fastbuild.run_compiler, original_runner)
                return output, status

            # Only configuration is substituted: staging, slot locks, Cargo,
            # compiler subprocess, linker, objcopy and remark parsing are real.
            for lines in (False, True):
                with self.subTest(lines=lines):
                    output, status = run_capture(lines, str(lines))
                    self.assertTrue((output / 'unstripped.so').read_bytes().startswith(b'\x7fELF'))
                    rows = json.loads((output / 'inline-remarks.json').read_text())
                    self.assertTrue(rows, (output / 'build.log').read_text()[-6000:])
                    self.assertTrue(any('arithmetic' in row['callee'] for row in rows), rows)
                    if lines:
                        self.assertTrue(any(row['loc'] for row in rows), rows)
                    self.assertEqual(status, 0)
            (source / 'src/lib.rs').write_text('this is not valid Rust\n')
            output, status = run_capture(False, 'compiler-error')
            self.assertEqual(status, 1)
            self.assertFalse((output / 'unstripped.so').exists())
            self.assertIn('error:', (output / 'build.log').read_text())


if __name__ == '__main__':
    unittest.main()
