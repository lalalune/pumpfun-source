"""Real patch/Git composition must not depend on the caller's text locale."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).with_name('integrate.py')


@unittest.skipIf(sys.platform == 'win32', 'requires a POSIX ASCII locale')
@unittest.skipUnless(all(shutil.which(tool) for tool in ('git', 'diff', 'patch')),
                     'requires real composition tools')
class CompositionLocaleTests(unittest.TestCase):
    def compose(self, kind):
        with tempfile.TemporaryDirectory(prefix='compose-locale-') as directory:
            root = Path(directory) / 'caf\N{LATIN SMALL LETTER E WITH ACUTE}'
            tool = root / 'reconstruction/harness/integrate.py'
            tool.parent.mkdir(parents=True)
            for name in ('integrate.py', 'treediff.py', 'source_inputs.py'):
                shutil.copyfile(TOOL.with_name(name), tool.with_name(name))
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            contents = {'Cargo.toml': b'[package]\nname="fixture"\nversion="0.1.0"\n',
                        'Cargo.lock': b'version = 3\n',
                        'src/lib.rs': b'pub fn value() -> u64 { 1 }\n'}
            name = ('src/caf\N{LATIN SMALL LETTER E WITH ACUTE}.rs'
                    if kind == 'text' else 'src/payload.bin')
            before, after = ((b'// before\n', b'// after\n') if kind == 'text'
                             else (b'\x00before', b'\x00after'))
            for label, data in [('base', before), ('part', after)]:
                for filename, value in {**contents, name: data}.items():
                    path = root / label / filename
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(value)
            env = dict(os.environ, LC_ALL='C', LANG='C', PYTHONUTF8='0',
                       PYTHONCOERCECLOCALE='0')
            # Isolate this locale regression from unrelated Git caller overrides.
            env = {key: value for key, value in env.items()
                   if not key.upper().startswith('GIT_')}
            if kind == 'text':
                filesystem = subprocess.check_output(
                    [sys.executable, '-c', 'import sys;print(sys.getfilesystemencoding())'],
                    env=env).decode().strip().lower().replace('-', '')
                if filesystem != 'utf8':
                    self.skipTest('requires UTF-8 filenames with a non-UTF-8 text locale')
            result = subprocess.run(
                [sys.executable, '-B', str(tool), '--name', 'locale',
                 '--base-src', str(root / 'base'), '--part', f'change={root / "part"}',
                 '--no-build'], env=env, capture_output=True, timeout=30)
            out = root / 'reconstruction/integ/locale'
            report = json.loads((out / 'report.json').read_bytes())
            self.assertEqual(result.returncode, 0, (result.stdout, result.stderr, report))
            self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                              'files': [name]}])
            self.assertEqual((out / 'src' / name).read_bytes(), after)
            self.assertEqual((root / 'base' / name).read_bytes(), before)
            self.assertEqual((root / 'part' / name).read_bytes(), after)
            self.assertFalse((root / '.git/index').exists())

    def test_text_patch_with_unicode_filename_in_ascii_locale(self):
        self.compose('text')

    def test_git_patch_beneath_unicode_repository_in_ascii_locale(self):
        self.compose('binary')


if __name__ == '__main__':
    unittest.main()
