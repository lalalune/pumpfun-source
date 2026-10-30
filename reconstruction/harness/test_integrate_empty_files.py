"""Compose actual crate snapshots, including empty-file existence changes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).with_name('integrate.py')


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


@unittest.skipUnless(shutil.which('git') and shutil.which('diff') and shutil.which('patch'),
                     'requires the real composition tools')
class EmptyFileCompositionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='compose-empty-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tool = self.root / 'reconstruction/harness/integrate.py'
        self.tool.parent.mkdir(parents=True)
        shutil.copyfile(TOOL, self.tool)

    def crate(self, name, files):
        root = self.root / name
        contents = {'Cargo.toml': b'[package]\nname="fixture"\nversion="0.1.0"\n',
                    'Cargo.lock': b'version = 3\n',
                    'src/lib.rs': b'pub fn value() -> u64 { 1 }\n', **files}
        for filename, data in contents.items():
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return root

    def compose(self, base, *parts):
        argv = [sys.executable, '-B', str(self.tool), '--name', 'test',
                '--base-src', str(base), '--no-build']
        for index, part in enumerate(parts):
            argv += ['--part', f'part{index}={part}']
        result = subprocess.run(argv, cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = self.root / 'reconstruction/integ/test'
        return output, json.loads((output / 'report.json').read_bytes())

    def roundtrip(self, before, after, changed, inside_git=False):
        if inside_git:
            subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
            # Git's host configuration must not translate snapshot bytes.
            subprocess.run(['git', '-C', str(self.root), 'config', 'core.autocrlf', 'true'], check=True)
        base, part = self.crate('base', before), self.crate('part', after)
        original = [snapshot(path) for path in (base, part)]
        output, report = self.compose(base, part)
        self.assertEqual(snapshot(output / 'src'), original[1])
        self.assertEqual([snapshot(path) for path in (base, part)], original)
        if inside_git:
            self.assertFalse((self.root / '.git/index').exists())
        self.assertEqual(report['parts'], [{'label': 'part0', 'status': 'applied',
                                           'files': sorted(changed)}])
        self.assertNotIn('build', report)
        self.assertNotIn('score', report)
        # The retained patch alone must reproduce the full intended tree.
        patch = output / 'parts/part0.patch'
        if patch.read_bytes().startswith(b'diff --git '):
            command = ['git', '-c', 'core.autocrlf=false', 'apply', '--no-index',
                       '-p2', '--whitespace=nowarn', str(patch)]
        else:
            command = ['patch', '-p2', '--forward', '-E', '-i', str(patch)]
            if sys.platform == 'win32':
                command.append('--binary')
        # A detached replay directory keeps Git's caller-prefix filtering out
        # of this independent patch portability check.
        with tempfile.TemporaryDirectory(prefix='compose-patch-replay-') as directory:
            detached = Path(directory) / 'crate'
            shutil.copytree(base, detached)
            applied = subprocess.run(command, cwd=detached, capture_output=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(snapshot(detached), original[1])
        return output

    def test_empty_addition(self):
        self.roundtrip({}, {'src/empty.rs': b''}, ['src/empty.rs'])

    def test_empty_deletion(self):
        self.roundtrip({'src/empty.rs': b''}, {}, ['src/empty.rs'])

    def test_existing_file_becomes_empty(self):
        self.roundtrip({'src/empty.rs': b'// prior implementation\n'},
                       {'src/empty.rs': b''}, ['src/empty.rs'])

    def test_empty_file_becomes_nonempty(self):
        self.roundtrip({'src/empty.rs': b''}, {'src/empty.rs': b'// implementation\n'},
                       ['src/empty.rs'])

    @unittest.skipIf(sys.platform == 'win32', 'Windows forbids tab/newline filenames')
    def test_empty_filename_with_tabs_and_newlines(self):
        name = 'src/empty\tline\né.rs'
        self.roundtrip({}, {name: b''}, [name])

    def test_mixed_changes_preserve_quoted_paths_and_carriage_returns_in_a_repo(self):
        old = b'// context\r\npub fn value() -> u64 { 1 }\n// tail\r\n'
        self.roundtrip({'src/lib.rs': old, 'src/gone.rs': b'', 'src/emptied.rs': b'// old\n'},
                       {'src/lib.rs': old.replace(b'{ 1 }', b'{ 2 }'),
                        'src/emptied.rs': b'', 'src/café space.rs': b''},
                       ['src/lib.rs', 'src/gone.rs', 'src/emptied.rs', 'src/café space.rs'],
                       inside_git=True)

    @unittest.skipUnless(shutil.which('rustc'), 'requires a native Rust compiler')
    def test_adding_an_empty_module_keeps_the_composed_crate_compilable(self):
        base = self.crate('base', {})
        part = self.crate('part', {'src/lib.rs': b'pub mod added;\n', 'src/added.rs': b''})
        output, report = self.compose(base, part)
        for name, source in [('base', base), ('part', part), ('composed', output / 'src')]:
            with self.subTest(source=name):
                result = subprocess.run(
                    ['rustc', '--crate-type', 'lib', '--emit=metadata', str(source / 'src/lib.rs'),
                     '-o', str(self.root / (name + '.rmeta'))], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report['parts'][0]['files'], ['src/added.rs', 'src/lib.rs'])

    def test_empty_addition_conflicts_with_an_earlier_nonempty_addition(self):
        base = self.crate('base', {})
        first = self.crate('first', {'src/empty.rs': b'// keep earlier contribution\n'})
        second = self.crate('second', {'src/empty.rs': b'',
                                       'src/lib.rs': b'pub fn value() -> u64 { 2 }\n'})
        output, report = self.compose(base, first, second)
        self.assertEqual([part['status'] for part in report['parts']], ['applied', 'conflict'])
        self.assertEqual(snapshot(output / 'src'), snapshot(first))

    def test_empty_deletion_conflicts_with_an_earlier_content_change(self):
        base = self.crate('base', {'src/empty.rs': b''})
        first = self.crate('first', {'src/empty.rs': b'// keep earlier contribution\n'})
        second = self.crate('second', {})
        output, report = self.compose(base, first, second)
        self.assertEqual([part['status'] for part in report['parts']], ['applied', 'conflict'])
        self.assertEqual(snapshot(output / 'src'), snapshot(first))


if __name__ == '__main__':
    unittest.main()
