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


if __name__ == '__main__':
    unittest.main()
