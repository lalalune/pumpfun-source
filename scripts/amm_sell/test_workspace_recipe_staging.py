"""Compiler-free regression checks for AMM staging output containment.

Run from the repository root:
    python3 -I -B scripts/amm_sell/test_workspace_recipe_staging.py

The inputs are authored temporary Cargo/source fixtures. Tests execute the real
public staging CLI with an empty PATH, not Cargo, a compiler, SDK or program.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest


RECIPE = Path(__file__).with_name('workspace_recipe.py')
MEMBERS = ('programs/pump-amm', 'crates/native-transfer-fee')


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        if path.is_file():
            result[relative] = ('file', hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir():
            result[relative] = ('directory',)
        else:
            raise AssertionError('unexpected source path: ' + relative)
    return result


class SourceContainmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.files = {
            'programs/pump-amm/Cargo.toml': b'''[package]
name = "pump-amm-recovered"
version = "0.1.0"
edition = "2021"
[dependencies]
native-transfer-fee = { path = "../../crates/native-transfer-fee" }
[profile.release]
panic = "abort"
overflow-checks = true
[workspace]
''',
            'programs/pump-amm/Cargo.lock': b'# authored fixture lockfile\nversion = 3\n',
            'programs/pump-amm/src/lib.rs': b'// authored fixture; never compiled\npub fn main() {}\n',
            'programs/pump-amm/idls/pump.json': b'{"authoredFixture":true}\n',
            'crates/native-transfer-fee/Cargo.toml': b'''[package]
name = "native-transfer-fee"
version = "0.1.0"
edition = "2021"
''',
            'crates/native-transfer-fee/src/lib.rs': b'// authored dependency fixture; never compiled\n',
        }
        for relative, raw in self.files.items():
            path = self.source / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def stage(self, output):
        return subprocess.run(
            [sys.executable, '-I', '-B', str(RECIPE), 'stage',
             '--source-root', str(self.source), '--output', str(output)],
            env={'PATH': '', 'PYTHONDONTWRITEBYTECODE': '1'},
            cwd=self.root, capture_output=True, text=True,
        )

    def assert_rejected_without_source_changes(self, output):
        before = inventory(self.source)
        result = self.stage(output)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(output.exists(), 'stager wrote the rejected output')
        self.assertEqual(inventory(self.source), before, 'stager changed input bytes or membership')

    def test_safe_output_preserves_source_and_stages_exact_rust(self):
        before = inventory(self.source)
        output = self.root / 'safe' / 'workspace'
        result = self.stage(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['verified'])
        self.assertEqual(report['rust_transformations'], 0)
        self.assertEqual(inventory(self.source), before)
        for relative, raw in self.files.items():
            if relative.endswith('.rs') or relative.endswith('.json'):
                self.assertEqual((output / relative).read_bytes(), raw)
        self.assertEqual((output / 'Cargo.lock').read_bytes(), self.files['programs/pump-amm/Cargo.lock'])
        self.assertFalse((output / 'programs/pump-amm/Cargo.lock').exists())

    def test_output_under_main_crate_is_rejected_before_writing(self):
        self.assert_rejected_without_source_changes(self.source / MEMBERS[0] / 'generated')

    def test_output_under_local_dependency_is_rejected_before_writing(self):
        self.assert_rejected_without_source_changes(self.source / MEMBERS[1] / 'generated')

    def test_alias_into_either_input_crate_is_rejected_before_writing(self):
        for index, member in enumerate(MEMBERS):
            with self.subTest(member=member):
                alias = self.root / ('input-alias-' + str(index))
                try:
                    alias.symlink_to(self.source / member, target_is_directory=True)
                except (OSError, NotImplementedError) as error:
                    self.skipTest('directory symlinks unavailable: ' + str(error))
                self.assert_rejected_without_source_changes(alias / 'generated')

    def test_alias_to_safe_external_output_still_works(self):
        actual = self.root / 'external'
        actual.mkdir()
        alias = self.root / 'external-alias'
        try:
            alias.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest('directory symlinks unavailable: ' + str(error))
        before = inventory(self.source)
        result = self.stage(alias / 'workspace')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(inventory(self.source), before)
        self.assertTrue((actual / 'workspace/Cargo.toml').is_file())

    def test_existing_output_is_preserved(self):
        output = self.root / 'existing'
        output.mkdir()
        marker = output / 'retained.txt'
        marker.write_bytes(b'authored retained output\n')
        before = inventory(self.source)
        result = self.stage(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Output must be a new directory', result.stderr)
        self.assertEqual(marker.read_bytes(), b'authored retained output\n')
        self.assertEqual(inventory(self.source), before)

    def test_safe_dotdot_output_does_not_create_parents_in_input_crate(self):
        before = {member: inventory(self.source / member) for member in MEMBERS}
        missing = self.source / MEMBERS[1] / 'missing-parent'
        output = missing / '..' / '..' / 'safe-workspace'
        canonical = output.resolve()
        result = self.stage(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((canonical / 'Cargo.toml').is_file())
        self.assertFalse(missing.exists(), 'lexical mkdir created a directory inside an input crate')
        self.assertEqual({member: inventory(self.source / member) for member in MEMBERS}, before)

    def test_canonical_existing_output_is_preserved_without_dotdot_parents(self):
        missing = self.source / MEMBERS[1] / 'missing-parent'
        output = missing / '..' / '..' / 'safe-workspace'
        canonical = output.resolve()
        canonical.mkdir()
        marker = canonical / 'retained.txt'
        marker.write_bytes(b'authored canonical output\n')
        before = {member: inventory(self.source / member) for member in MEMBERS}
        result = self.stage(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(missing.exists())
        self.assertIn('Output must be a new directory', result.stderr)
        self.assertEqual(marker.read_bytes(), b'authored canonical output\n')
        self.assertEqual({member: inventory(self.source / member) for member in MEMBERS}, before)


if __name__ == '__main__':
    unittest.main()
