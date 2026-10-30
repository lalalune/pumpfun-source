"""Persist real SBF compiler diagnostics under an uncoerced ASCII locale."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HARNESS = Path(__file__).resolve().parent
DRIVER = '''
import json, locale, sys
from pathlib import Path
import fastbuild
root, sdk = Path(sys.argv[1]), Path(sys.argv[2])
assert locale.getencoding().lower() in ('ascii', 'us-ascii', 'ansi_x3.4-1968')
assert sys.flags.utf8_mode == int(sys.argv[4])
fastbuild.SDK = sdk
fastbuild.RECIPES['identity'] = {'triple': 'sbf-solana-solana',
    'rustc': sdk / 'rust/bin/rustc', 'template': root / 'no-template'}
fastbuild.LOCKDIR = root / 'locks'
Path.home = classmethod(lambda cls: root / 'home')
result = fastbuild.build(root / 'source', root / 'work', root / 'output',
                         recipe='identity', quiet=sys.argv[3] == 'quiet')
print(json.dumps(result))
'''


@unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
class CompilerLogPersistenceTests(unittest.TestCase):
    def exercise(self, *, valid, quiet, metadata=False):
        with tempfile.TemporaryDirectory(prefix='pump-log-persistence-') as temporary:
            root = Path(temporary)
            source = root / 'source'
            (source / 'src').mkdir(parents=True)
            description = 'description="caf\u00e9"\n' if metadata else ''
            (source / 'Cargo.toml').write_text(
                '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n' + description +
                '[lib]\ncrate-type=["cdylib"]\n'
                '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n',
                encoding='utf-8')
            if metadata:
                (source / 'link').mkdir()
                (source / 'link/ordered.ld').write_bytes((HARNESS / 'sbf_default.ld').read_bytes())
            (source / 'Cargo.lock').write_text(
                'version=3\n[[package]]\nname="pump-recovered"\nversion="0.1.0"\n')
            code = ('#![no_std]\n'
                    '#[deprecated(note="caf\u00e9")] fn old(x:u64)->u64 { x.wrapping_add(1) }\n'
                    '#[no_mangle] pub extern "C" fn entrypoint(input:*const u64)->u64 {\n'
                    '    old(unsafe { core::ptr::read_volatile(input) })\n}\n'
                    '#[panic_handler] fn panic(_: &core::panic::PanicInfo)->! { loop {} }\n')
            if not valid:
                code += 'compile_error!("caf\u00e9");\n'
            (source / 'src/lib.rs').write_text(code, encoding='utf-8')
            env = dict(os.environ, LC_ALL='C', PYTHONUTF8='0', PYTHONCOERCECLOCALE='0',
                       PYTHONPATH=str(HARNESS))
            arguments = ['-c', DRIVER, str(root),
                         str(Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve()),
                         'quiet' if quiet else 'echo']
            control = subprocess.run([sys.executable, '-X', 'utf8=1', *arguments, '1'],
                                     env=env, capture_output=True)
            self.assertEqual(control.returncode, 0, control.stderr.decode('utf-8', errors='replace'))
            self.assertEqual(json.loads(control.stdout.splitlines()[-1])['ok'], valid)
            original_elf = (root / 'output/unstripped.so').read_bytes() if valid else None
            run = subprocess.run([sys.executable, '-X', 'utf8=0', *arguments, '0'],
                                 env=env, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', errors='replace'))
            result = json.loads(run.stdout.splitlines()[-1])
            self.assertEqual(result['ok'], valid)
            self.assertIn('caf\u00e9', (root / 'output/build.log').read_text(encoding='utf-8'))
            self.assertEqual((root / 'output/unstripped.so').exists(), valid)
            if valid:
                self.assertTrue((root / 'output/unstripped.so').read_bytes().startswith(b'\x7fELF'))
                self.assertEqual((root / 'output/unstripped.so').read_bytes(), original_elf)
            if not quiet:
                self.assertIn(b'caf\\xe9', run.stdout)

    def test_successful_build_retains_unicode_warnings(self):
        self.exercise(valid=True, quiet=True)

    def test_compiler_failure_retains_unicode_log_and_build_result(self):
        for quiet in (True, False):
            with self.subTest(quiet=quiet):
                self.exercise(valid=False, quiet=quiet)

    def test_unicode_cargo_metadata_survives_staging_and_link_configuration(self):
        self.exercise(valid=True, quiet=True, metadata=True)


if __name__ == '__main__':
    unittest.main()
