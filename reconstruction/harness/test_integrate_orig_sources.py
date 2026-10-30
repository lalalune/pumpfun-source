"""Composition may clean its own patch backups, never source named *.orig."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).with_name('integrate.py')
VENDORED = b'[package]\nname = "dep"\n'


@unittest.skipUnless(shutil.which('git') and shutil.which('diff') and shutil.which('patch'),
                     'requires the real composition tools')
class OrigSourceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='compose-orig-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tool = self.root / 'reconstruction/harness/integrate.py'
        self.tool.parent.mkdir(parents=True)
        shutil.copyfile(TOOL, self.tool)
        # integrate.py imports its sibling treediff module.
        shutil.copyfile(TOOL.with_name('treediff.py'), self.tool.with_name('treediff.py'))
        shutil.copyfile(TOOL.with_name('source_inputs.py'), self.tool.with_name('source_inputs.py'))

    def crate(self, name, library):
        root = self.root / name
        contents = {'Cargo.toml': b'[package]\nname="fixture"\nversion="0.1.0"\n',
                    'Cargo.lock': b'version = 3\n',
                    'src/lib.rs': library,
                    'vendor/dep/Cargo.toml.orig': VENDORED}
        for filename, data in contents.items():
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return root

    def compose(self, base, part):
        result = subprocess.run(
            [sys.executable, '-B', str(self.tool), '--name', 'test', '--base-src', str(base),
             '--part', f'part={part}', '--no-build'],
            cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.root / 'reconstruction/integ/test'
        self.assertEqual(json.loads((output / 'report.json').read_bytes())['parts'][0]['status'], 'applied')
        return output / 'src'

    def test_vendored_orig_file_survives_an_applied_part(self):
        base = self.crate('base', b'pub fn value() -> u64 { 1 }\n')
        part = self.crate('part', b'pub fn value() -> u64 { 2 }\n')
        composed = self.compose(base, part)
        self.assertEqual((composed / 'src/lib.rs').read_bytes(), b'pub fn value() -> u64 { 2 }\n')
        self.assertEqual((composed / 'vendor/dep/Cargo.toml.orig').read_bytes(), VENDORED)

    def test_patch_backups_are_still_removed(self):
        lines = [b'line %d\n' % number for number in range(1, 20)]
        base = self.crate('base', b''.join(lines))
        # Shifted context would ordinarily make patch write a .orig backup.
        changed = list(lines)
        changed[9] = b'changed\n'
        part = self.crate('part', b''.join(changed))
        (self.root / 'derived').mkdir()
        shifted = self.crate('derived/base', b'first\nsecond\n' + b''.join(lines))
        result = subprocess.run(
            [sys.executable, '-B', str(self.tool), '--name', 'test', '--base-src', str(shifted),
             '--part', f'part={part}', '--base-of', f'part={base}', '--no-build'],
            cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        composed = self.root / 'reconstruction/integ/test/src'
        self.assertIn(b'changed\n', (composed / 'src/lib.rs').read_bytes())
        self.assertEqual(sorted(path.relative_to(composed).as_posix() for path in composed.rglob('*.orig')),
                         ['vendor/dep/Cargo.toml.orig'])

    def test_offset_patch_cannot_overwrite_an_existing_source_backup_name(self):
        lines = [b'line %d\n' % number for number in range(1, 20)]
        base = self.crate('base', b''.join(lines))
        changed = list(lines); changed[9] = b'changed\n'
        part = self.crate('part', b''.join(changed))
        shifted = self.crate('shifted', b'first\nsecond\n' + b''.join(lines))
        (shifted/'src/lib.rs.orig').write_bytes(b'real source\n')
        result = subprocess.run(
            [sys.executable, '-B', str(self.tool), '--name', 'test', '--base-src', str(shifted),
             '--part', f'part={part}', '--base-of', f'part={base}', '--no-build'],
            cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        composed = self.root/'reconstruction/integ/test/src'
        self.assertEqual((composed/'src/lib.rs.orig').read_bytes(), b'real source\n')
        self.assertIn(b'changed\n', (composed/'src/lib.rs').read_bytes())

    def test_part_can_add_and_change_source_files_named_orig(self):
        base = self.crate('base', b'unchanged\n')
        part = self.crate('part', b'unchanged\n')
        (part/'vendor/dep/Cargo.toml.orig').write_bytes(b'changed source\n')
        (part/'src/new.orig').write_bytes(b'new source\n')
        composed = self.compose(base, part)
        self.assertEqual((composed/'vendor/dep/Cargo.toml.orig').read_bytes(), b'changed source\n')
        self.assertEqual((composed/'src/new.orig').read_bytes(), b'new source\n')


if __name__ == '__main__':
    unittest.main()
