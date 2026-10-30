"""Exercise manifest staging with real rsync and Cargo's offline parser."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

import fastbuild


@unittest.skipUnless(shutil.which('cargo') and shutil.which('rsync'), 'requires Cargo and rsync')
class ManifestHeaderTests(unittest.TestCase):
    def exercise(self, metadata='', comment='', workspace_comment=''):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, workspace = root / 'source', root / 'workspace'
            (source / 'src').mkdir(parents=True)
            text = ('[package]\nname="manifest-fixture"\nversion="0.1.0"\nedition="2021"\n'
                    + metadata + comment
                    + '[profile.release]\npanic="abort"\ncodegen-units=1\n'
                    + '[workspace]\n' + workspace_comment)
            (source / 'Cargo.toml').write_text(text)
            (source / 'Cargo.lock').write_text(
                'version = 3\n[[package]]\nname = "manifest-fixture"\nversion = "0.1.0"\n')
            (source / 'src/lib.rs').write_text('pub fn retained() -> u64 { 42 }\n')
            original = tomllib.loads(text)
            env = dict(os.environ, CARGO_HOME=str(root / 'cargo-home'))

            def cargo_metadata(manifest):
                run = subprocess.run(['cargo', 'metadata', '--offline', '--locked', '--no-deps',
                                      '--format-version', '1', '--manifest-path', str(manifest)],
                                     env=env, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                return json.loads(run.stdout)

            self.assertEqual(cargo_metadata(source / 'Cargo.toml')['packages'][0]['name'],
                             'manifest-fixture')
            crate = fastbuild.stage(source, workspace)
            staged = tomllib.loads((crate / 'Cargo.toml').read_text())
            self.assertEqual(staged['package'], original['package'])
            self.assertNotIn('profile', staged)
            self.assertNotIn('workspace', staged)
            self.assertEqual(tomllib.loads((workspace / 'Cargo.toml').read_text())['profile'],
                             original['profile'])
            self.assertEqual((crate / 'src/lib.rs').read_bytes(), (source / 'src/lib.rs').read_bytes())
            result = cargo_metadata(crate / 'Cargo.toml')
            self.assertEqual(Path(result['workspace_root']), workspace)
            self.assertEqual((source / 'Cargo.toml').read_text(), text)

    def test_plain_manifest_control(self):
        self.exercise()

    def test_commented_headers_are_not_table_boundaries(self):
        self.exercise(comment='# Keep [profile.release] and [workspace] below the dependencies.\n')

    def test_header_lines_inside_multiline_description_are_not_boundaries(self):
        self.exercise(metadata='description="""Example configuration:\n[profile.release]\n[workspace]\n"""\n')

    def test_empty_workspace_can_have_a_comment(self):
        self.exercise(workspace_comment='# This crate is independently buildable.\n')


if __name__ == '__main__':
    unittest.main()
