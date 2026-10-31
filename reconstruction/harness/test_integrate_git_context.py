"""Real composition commands must not inherit a caller's Git repository context."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent


class CompositionGitContextTests(unittest.TestCase):
    def test_foreign_git_context_preserves_binary_and_empty_file_changes(self):
        for change in ('binary', 'empty', 'text'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                harness = root / 'harness'
                harness.mkdir()
                for name in ('integrate.py', 'treediff.py', 'source_inputs.py'):
                    shutil.copyfile(HERE / name, harness / name)
                base, part = root / 'base', root / 'part'
                for source in (base, part):
                    (source / 'src').mkdir(parents=True)
                    (source / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.1.0"\n')
                    (source / 'Cargo.lock').write_text('version=3\n')
                    (source / 'src/lib.rs').write_text('pub const VALUE:u8=1;\n')
                if change == 'binary':
                    (base / 'data.bin').write_bytes(b'\x00first')
                    (part / 'data.bin').write_bytes(b'\x00other')
                elif change == 'empty':
                    (part / 'empty.txt').touch()
                else:
                    (part / 'src/lib.rs').write_text('pub const VALUE:u8=2;\n')
                external = root / 'external'
                external.mkdir()
                clean = {key: value for key, value in os.environ.items()
                         if not key.upper().startswith('GIT_')}
                subprocess.run(['git', '-C', str(external), 'init', '-q'],
                               env=clean, check=True, capture_output=True)
                marker = external / 'marker'
                marker.write_bytes(b'unrelated working tree')
                environment = dict(clean, GIT_DIR=str(external / '.git'),
                                   GIT_WORK_TREE=str(external), GIT_INDEX_FILE=str(external / 'index'))
                result = subprocess.run([
                    sys.executable, '-B', str(harness / 'integrate.py'), '--name', 'composition',
                    '--base-src', str(base), '--part', 'change=' + str(part), '--no-build'],
                    env=environment, text=True, capture_output=True, timeout=20)
                output = root / 'integ/composition'
                report = json.loads((output / 'report.json').read_text())
                self.assertEqual(result.returncode, 0, result.stderr + json.dumps(report))
                self.assertEqual(report['parts'][0]['status'], 'applied')
                expected = {p.relative_to(part): p.read_bytes() for p in part.rglob('*') if p.is_file()}
                actual = {p.relative_to(output / 'src'): p.read_bytes()
                          for p in (output / 'src').rglob('*') if p.is_file()}
                self.assertEqual(actual, expected)
                self.assertEqual(marker.read_bytes(), b'unrelated working tree')
                self.assertFalse((external / 'index').exists())


if __name__ == '__main__':
    unittest.main()
