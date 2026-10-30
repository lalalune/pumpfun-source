"""Run file-only composition through the actual CLI and installed diff/patch."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid


TOOL = Path(__file__).resolve().with_name('integrate.py')


@unittest.skipUnless(shutil.which('diff') and shutil.which('patch'), 'requires real diff and patch')
class NoBuildCompositionTests(unittest.TestCase):
    def assert_composition(self, before, after):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, part = root / 'base', root / 'part'
            for source, contents in ((base, before), (part, after)):
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_bytes(b'[package]\nname="fixture"\nversion="0.0.0"\n')
                (source / 'Cargo.lock').write_bytes(b'version = 3\n')
                (source / 'src/lib.rs').write_bytes(contents)
            def snapshot(source):
                return {p.relative_to(source).as_posix(): p.read_bytes()
                        for p in source.rglob('*') if p.is_file()}
            original_base, original_part = snapshot(base), snapshot(part)
            name = 'test-no-build-' + uuid.uuid4().hex
            output = TOOL.parent.parent / 'integ' / name
            def remove_owned(path):
                if path.exists():
                    path.resolve().relative_to((TOOL.parent.parent / 'integ').resolve())
                    shutil.rmtree(path)
            self.addCleanup(remove_owned, output)
            scratch = output.parent / '.tmp' / name
            self.addCleanup(remove_owned, scratch)
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--name', name,
                '--base-src', str(base), '--part', 'change=' + str(part), '--no-build'],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(snapshot(output / 'src'), original_part)
            self.assertEqual(snapshot(base), original_base)
            self.assertEqual(snapshot(part), original_part)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                               'files': ['src/lib.rs']}])
            self.assertNotIn('build', report)
            self.assertNotIn('score', report)
            self.assertIn(b'+pub fn recovered_value() -> u64 { 2 }',
                          (output / 'parts/change.patch').read_bytes())

    def test_cli_composes_lf_source_without_loading_the_builder(self):
        self.assert_composition(b'pub fn recovered_value() -> u64 { 1 }\n',
                                b'pub fn recovered_value() -> u64 { 2 }\n')

    def test_cli_preserves_crlf_source_bytes(self):
        before = b'// context\r\npub fn recovered_value() -> u64 { 1 }\r\n'
        self.assert_composition(before, before.replace(b'{ 1 }', b'{ 2 }'))

    def test_cli_preserves_mixed_line_endings(self):
        before = b'// context\r\npub fn recovered_value() -> u64 { 1 }\n// tail\r\n'
        self.assert_composition(before, before.replace(b'{ 1 }', b'{ 2 }'))

    def test_cli_preserves_absent_final_newline(self):
        before = b'// context\r\npub fn recovered_value() -> u64 { 1 }'
        self.assert_composition(before, before.replace(b'{ 1 }', b'{ 2 }'))

    def compose(self, base_files, part_files):
        """Compose one part through the CLI; return (src snapshot, report)."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source, files in ((root / 'base', base_files), (root / 'part', part_files)):
                files = {'Cargo.toml': b'[package]\nname="fixture"\nversion="0.0.0"\n',
                         'Cargo.lock': b'version = 3\n', **files}
                for name, contents in files.items():
                    (source / name).parent.mkdir(parents=True, exist_ok=True)
                    (source / name).write_bytes(contents)
            name = 'test-no-build-' + uuid.uuid4().hex
            integ = TOOL.parent.parent / 'integ'
            for owned in (integ / name, integ / '.tmp' / name):
                self.addCleanup(lambda path=owned: path.exists() and shutil.rmtree(path))
            result = subprocess.run([sys.executable, '-B', str(TOOL), '--name', name,
                '--base-src', str(root / 'base'), '--part', 'change=' + str(root / 'part'),
                '--no-build'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            src = integ / name / 'src'
            return ({p.relative_to(src).as_posix(): p.read_bytes() for p in src.rglob('*') if p.is_file()},
                    json.loads((integ / name / 'report.json').read_text()))

    def test_nested_target_sources_compose_but_root_build_directory_does_not(self):
        # fastbuild stages nested target directories as source (#1531); only the
        # crate-root build directory is excluded. Composition must keep the same set.
        base = {'src/lib.rs': b'pub mod target;\n', 'src/target/mod.rs': b'pub const VALUE: u8 = 1;\n',
                'assets/target/data.bin': b'\x00\xff\n', 'target/release/stale.o': b'build output'}
        part = dict(base, **{'src/target/mod.rs': b'pub const VALUE: u8 = 2;\n',
                             'target/release/stale.o': b'other build output'})
        files, report = self.compose(base, part)
        expected = {k: v for k, v in part.items() if not k.startswith('target/')}
        self.assertEqual({k: v for k, v in files.items() if k not in ('Cargo.toml', 'Cargo.lock')}, expected)
        self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                           'files': ['src/target/mod.rs']}])

    def test_regular_file_named_target_is_a_composed_source_input(self):
        asset = b'source asset\x00'
        base = {'src/lib.rs': b'pub const DATA: &[u8] = include_bytes!("../target");\n', 'target': asset}
        part = dict(base, **{'src/lib.rs': base['src/lib.rs'] + b'pub const LEN: usize = DATA.len();\n'})
        files, report = self.compose(base, part)
        self.assertEqual(files.get('target'), asset)
        self.assertEqual(files['src/lib.rs'], part['src/lib.rs'])
        self.assertEqual(report['parts'][0]['status'], 'applied')


HERE = Path(__file__).resolve().parent


def crate(path):
    (path / 'src').mkdir(parents=True)
    (path / 'Cargo.toml').write_bytes(b'[package]\nname="fixture"\nversion="0.0.0"\n')
    (path / 'Cargo.lock').write_bytes(b'version = 3\n')
    (path / 'src/lib.rs').write_bytes(b'pub fn fixture() {}\n')
    return path


def contents(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in path.rglob('*') if p.is_file()}


class IntegrationScratchOverlapTests(unittest.TestCase):
    def stage_cli(self, root):
        harness = root / 'reconstruction/harness'
        harness.mkdir(parents=True)
        for name in ('integrate.py', 'treediff.py'):
            shutil.copyfile(HERE / name, harness / name)
        return harness / 'integrate.py'

    def test_nonportable_labels_fail_before_creating_output(self):
        for value in ('A.', 'CON', 'nul.part', 'Lpt1', 'COM9.x'):
            for role in ('name', 'part', 'base-of'):
                with self.subTest(value=value, role=role), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    cli = self.stage_cli(root)
                    base, part = (crate(root / name) for name in ('base', 'part'))
                    before = contents(root)
                    arguments = ['--name', value if role == 'name' else 'trial',
                                 '--base-src', str(base)]
                    if role != 'name':
                        arguments += ['--part', (value if role == 'part' else 'A') + '=' + str(part)]
                    if role == 'base-of':
                        arguments += ['--base-of', value + '=' + str(base)]
                    result = subprocess.run([sys.executable, '-B', str(cli), '--no-build', *arguments],
                                            capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn('nonportable composition name or label', result.stderr)
                    self.assertFalse((root / 'reconstruction/integ').exists())
                    self.assertEqual(contents(root), before)

    def test_base_overrides_reject_folded_duplicates_and_require_exact_spelling(self):
        for overrides, message in ((('A', 'a'), 'duplicate label'),
                                   (('a',), 'base overrides have no matching part')):
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                cli = self.stage_cli(root)
                base, part = (crate(root / name) for name in ('base', 'part'))
                before = contents(root)
                arguments = ['--name', 'trial', '--base-src', str(base), '--part', 'A=' + str(part)]
                for value in overrides:
                    arguments += ['--base-of', value + '=' + str(base)]
                result = subprocess.run([sys.executable, '-B', str(cli), '--no-build', *arguments],
                                        capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(message, result.stderr)
                self.assertFalse((root / 'reconstruction/integ').exists())
                self.assertEqual(contents(root), before)

    @unittest.skipUnless(shutil.which('git'), 'requires real Git for the baseline reproduction')
    def test_case_colliding_labels_preserve_separate_patch_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cli = self.stage_cli(root)
            base, one, two = (crate(root / name) for name in ('base', 'one', 'two'))
            (one / 'one.bin').write_bytes(b'')
            (two / 'two.bin').write_bytes(b'')
            before = [contents(path) for path in (base, one, two)]
            result = subprocess.run(
                [sys.executable, str(cli), '--no-build', '--name', 'trial',
                 '--base-src', str(base), '--part', 'A=' + str(one), '--part', 'a=' + str(two)],
                capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('duplicate label', result.stderr)
            self.assertFalse((root / 'reconstruction/integ/trial').exists())
            self.assertEqual([contents(path) for path in (base, one, two)], before)

    @unittest.skipUnless(shutil.which('git'), 'requires real Git patch application')
    def test_distinct_labels_retain_both_applied_patches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cli = self.stage_cli(root)
            base, one, two = (crate(root / name) for name in ('base', 'one', 'two'))
            (one / 'one.bin').write_bytes(b'')
            (two / 'two.bin').write_bytes(b'')
            before = [contents(path) for path in (base, one, two)]
            result = subprocess.run(
                [sys.executable, str(cli), '--no-build', '--name', 'control',
                 '--base-src', str(base), '--part', 'Change.v1=' + str(one),
                 '--base-of', 'Change.v1=' + str(base), '--part', 'Other-part=' + str(two)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            out = root / 'reconstruction/integ/control'
            report = json.loads((out / 'report.json').read_text())
            self.assertEqual([part['status'] for part in report['parts']], ['applied', 'applied'])
            self.assertIn('one.bin', (out / 'parts/Change.v1.patch').read_text())
            self.assertIn('two.bin', (out / 'parts/Other-part.patch').read_text())
            self.assertEqual(contents(out / 'src'), {**before[0], 'one.bin': b'', 'two.bin': b''})
            self.assertEqual([contents(path) for path in (base, one, two)], before)

    def test_scratch_overlaps_preserved_in_every_input_role(self):
        cases = [(role, relative) for role in ('base', 'part', 'derived')
                 for relative in ('unit/input', 'unit', '.')]
        for role, relative in cases:
            with self.subTest(role=role, relative=relative), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                cli = self.stage_cli(root)
                inputs = {name: crate(root / name) for name in ('base', 'part', 'derived')
                          if name != role}
                inputs[role] = crate(root / 'reconstruction/integ/.tmp/trial' / relative)
                before = {name: contents(path) for name, path in inputs.items()}
                completed = subprocess.run(
                    [sys.executable, str(cli), '--no-build', '--name', 'trial',
                     '--base-src', str(inputs['base']), '--part', 'unit=' + str(inputs['part']),
                     '--base-of', 'unit=' + str(inputs['derived'])], capture_output=True, text=True)
                self.assertEqual({name: contents(path) for name, path in inputs.items()}, before,
                                 completed.stderr)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn('source overlaps composition scratch', completed.stderr)
                self.assertFalse((root / 'reconstruction/integ/trial').exists())

    def test_nonoverlapping_no_build_composition_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cli = self.stage_cli(root)
            source = crate(root / 'base')
            before = contents(source)
            completed = subprocess.run(
                [sys.executable, str(cli), '--no-build', '--name', 'control',
                 '--base-src', str(source)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            out = root / 'reconstruction/integ/control'
            self.assertEqual(contents(out / 'src'), before)
            self.assertEqual(contents(source), before)
            self.assertEqual(json.loads((out / 'report.json').read_text())['parts'], [])


def directory_contents(root):
    return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_dir()}


def crate_tree(path, files, directories):
    (path / 'src').mkdir(parents=True)
    (path / 'Cargo.toml').write_bytes(b'[package]\nname="fixture"\nversion="0.0.0"\n')
    (path / 'Cargo.lock').write_bytes(b'version = 3\n')
    for name in directories:
        (path / name).mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        target = path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


@unittest.skipUnless(shutil.which('diff') and shutil.which('patch'), 'requires real diff and patch')
class DirectoryCompositionTests(unittest.TestCase):
    """Composition matches the part's directory set, not only its files."""

    def compose(self, base_files, base_dirs, parts):
        root = Path(tempfile.mkdtemp(prefix='integrate-directories-'))
        self.addCleanup(shutil.rmtree, root, True)
        base = root / 'base'
        crate_tree(base, base_files, base_dirs)
        inputs = [base]
        name = 'test-no-build-' + uuid.uuid4().hex
        arguments = ['--name', name, '--base-src', str(base), '--no-build']
        for label, files, dirs in parts:
            part = root / label
            crate_tree(part, files, dirs)
            inputs.append(part)
            arguments += ['--part', label + '=' + str(part)]
        def snapshot(path):
            return ({p.relative_to(path).as_posix(): (p.read_bytes(), bool(p.stat().st_mode & 0o111))
                     for p in path.rglob('*') if p.is_file()}, directory_contents(path))
        before = [snapshot(path) for path in inputs]
        integ = TOOL.parent.parent / 'integ'
        self.addCleanup(shutil.rmtree, integ / name, True)
        self.addCleanup(shutil.rmtree, integ / '.tmp' / name, True)
        result = subprocess.run([sys.executable, '-B', str(TOOL), *arguments],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([snapshot(path) for path in inputs], before)
        src = integ / name / 'src'
        files = {p.relative_to(src).as_posix(): p.read_bytes() for p in src.rglob('*') if p.is_file()}
        report = json.loads((integ / name / 'report.json').read_text())
        return files, directory_contents(src), report

    def source_files(self, files):
        return {name: data for name, data in files.items() if name not in ('Cargo.toml', 'Cargo.lock')}

    def test_deleted_last_file_removes_directories_absent_from_the_part(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n', 'src/old/deep/only.rs': b'// removed\n'}
        part = {'src/lib.rs': b'pub fn fixture() {}\n'}
        files, dirs, report = self.compose(base, (), [('change', part, ())])
        self.assertEqual(dirs, {'src'})
        self.assertEqual(self.source_files(files), part)
        self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                           'files': ['src/old/deep/only.rs'],
                                           'directories': {'removed': ['src/old', 'src/old/deep']}}])

    def test_part_that_only_adds_empty_directories_is_applied(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n'}
        files, dirs, report = self.compose(base, (), [('change', dict(base), ('src/new/leaf',))])
        self.assertEqual(dirs, {'src', 'src/new', 'src/new/leaf'})
        self.assertEqual(self.source_files(files), base)
        self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied', 'files': [],
                                           'directories': {'added': ['src/new', 'src/new/leaf']}}])

    def test_part_that_only_removes_an_empty_directory_is_applied(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n'}
        files, dirs, report = self.compose(base, ('src/empty',), [('change', dict(base), ())])
        self.assertEqual(dirs, {'src'})
        self.assertEqual(self.source_files(files), base)
        self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied', 'files': [],
                                           'directories': {'removed': ['src/empty']}}])

    def test_directory_removal_keeps_files_composed_by_another_part(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n'}
        kept = {'src/shared/keep.rs': b'// kept\n'}
        files, dirs, report = self.compose(
            base, ('src/shared',),
            [('add', {**base, **kept}, ('src/shared',)), ('remove', dict(base), ())])
        self.assertEqual(files['src/shared/keep.rs'], b'// kept\n')
        self.assertIn('src/shared', dirs)
        self.assertEqual(report['parts'][1], {'label': 'remove', 'status': 'applied', 'files': [],
                                              'directories': {'removed': ['src/shared'],
                                                              'retained': ['src/shared']}})

    def test_unchanged_part_stays_empty(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n'}
        _, dirs, report = self.compose(base, (), [('same', dict(base), ())])
        self.assertEqual(dirs, {'src'})
        self.assertEqual(report['parts'], [{'label': 'same', 'status': 'empty'}])

    def test_directory_conflict_preserves_earlier_parts_and_skips_all_new_changes(self):
        base = {'src/lib.rs': b'pub fn before() {}\n'}
        first = {**base, 'occupied': b'earlier file'}
        second = {'src/lib.rs': b'pub fn should_not_apply() {}\n'}
        files, dirs, report = self.compose(
            base, (), [('first', first, ()), ('second', second, ('occupied',))])
        self.assertEqual(self.source_files(files), first)
        self.assertNotIn('occupied', dirs)
        self.assertEqual(report['parts'][1]['status'], 'conflict')
        self.assertIn('directory composition conflict', report['parts'][1]['detail'])

    def test_file_replacing_directory_is_not_reported_as_retained_directory(self):
        base = {'src/lib.rs': b'pub fn fixture() {}\n', 'src/node/child.rs': b'old'}
        part = {'src/lib.rs': base['src/lib.rs'], 'src/node': b'replacement file'}
        files, dirs, report = self.compose(base, (), [('replace', part, ())])
        self.assertEqual(self.source_files(files), part)
        self.assertNotIn('src/node', dirs)
        self.assertEqual(report['parts'][0]['directories'], {'removed': ['src/node']})


if __name__ == '__main__':
    unittest.main()
