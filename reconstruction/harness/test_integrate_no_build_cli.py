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
    def test_cli_composes_source_without_loading_the_builder(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, part = root / 'base', root / 'part'
            before = b'pub fn recovered_value() -> u64 { 1 }\n'
            after = b'pub fn recovered_value() -> u64 { 2 }\n'
            for source, contents in ((base, before), (part, after)):
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_bytes(b'[package]\nname="fixture"\nversion="0.0.0"\n')
                (source / 'Cargo.lock').write_bytes(b'version = 3\n')
                (source / 'src/lib.rs').write_bytes(contents)
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
            self.assertEqual((output / 'src/src/lib.rs').read_bytes(), after)
            self.assertEqual((base / 'src/lib.rs').read_bytes(), before)
            self.assertEqual((part / 'src/lib.rs').read_bytes(), after)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['parts'], [{'label': 'change', 'status': 'applied',
                                               'files': ['src/lib.rs']}])
            self.assertNotIn('build', report)
            self.assertNotIn('score', report)
            self.assertIn(b'+pub fn recovered_value() -> u64 { 2 }',
                          (output / 'parts/change.patch').read_bytes())


if __name__ == '__main__':
    unittest.main()
