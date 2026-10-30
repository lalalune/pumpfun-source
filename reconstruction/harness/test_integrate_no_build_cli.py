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


if __name__ == '__main__':
    unittest.main()
