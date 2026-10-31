"""Cargo configs outside the crate must not change the staged release recipe.

Exercise the real staging path. Compiler boundaries are controlled; no SDK,
program build or VM is run.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fastbuild

MANIFEST = '''[package]
name = "pump-recovered"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[profile.release]
opt-level = 3

[workspace]
'''
PROFILE = '[profile.release]\nopt-level = 0\n'


@unittest.skipUnless(shutil.which('rsync'), 'fastbuild staging requires rsync')
class CargoConfigTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'source'
        (self.source / 'src').mkdir(parents=True)
        (self.source / 'Cargo.toml').write_text(MANIFEST, encoding='utf-8')
        (self.source / 'Cargo.lock').write_text('version = 3\n', encoding='utf-8')
        (self.source / 'src/lib.rs').write_text('', encoding='utf-8')
        self.home = self.root / 'home'
        self.home.mkdir()
        self.work = self.root / 'lanes/one/work'
        self.out = self.root / 'lanes/one/out'
        self.out.mkdir(parents=True)
        self.previous = self.out / 'unstripped.so'
        self.previous.write_bytes(b'prior binary')

    def build(self):
        compiled = []

        def compiler(command, **_options):
            compiled.append(command)
            return subprocess.CompletedProcess(command, 1, stdout='stopped by the test\n'), False

        sdk = self.root / 'sdk'
        recipe = {'triple': 'sbpf-solana-solana', 'rustc': sdk / 'rustc', 'template': self.root / 'absent'}
        with patch.dict(os.environ, {'HOME': str(self.home)}), \
                patch.dict(fastbuild.RECIPES, {'identity': recipe}), \
                patch.object(fastbuild, 'LOCKDIR', self.root / 'locks'), \
                patch.object(fastbuild, 'run_compiler', compiler):
            try:
                result = fastbuild.build(self.source, self.work, self.out, quiet=True, recipe='identity')
            except ValueError as error:
                return str(error), compiled
        return result, compiled

    def write_config(self, directory, name='config.toml'):
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PROFILE, encoding='utf-8')
        return path

    def assert_refused(self, path):
        result, compiled = self.build()
        self.assertEqual(compiled, [], 'cargo ran under a config that overrides the staged profile')
        self.assertIsInstance(result, str)
        self.assertIn('unreviewed Cargo config', result)
        self.assertIn(str(path), result)
        self.assertEqual(self.previous.read_bytes(), b'prior binary')

    def test_parent_of_the_work_directory(self):
        self.assert_refused(self.write_config(self.root / 'lanes/.cargo'))

    def test_legacy_file_name(self):
        self.assert_refused(self.write_config(self.root / '.cargo', 'config'))

    def test_workspace_directory_itself(self):
        self.assert_refused(self.write_config(self.work / 'ws/.cargo'))

    def test_cargo_home(self):
        self.assert_refused(self.write_config(self.home / '.cargo'))

    def test_dangling_link(self):
        link = self.root / 'lanes/.cargo/config.toml'
        link.parent.mkdir(parents=True)
        link.symlink_to(self.root / 'absent.toml')
        self.assert_refused(link)

    def test_crate_config_stays_an_ignored_source_file(self):
        # Cargo starts from the workspace, so this file is hashed but never read.
        self.write_config(self.source / '.cargo')
        result, compiled = self.build()
        self.assertEqual(len(compiled), 1)
        self.assertIs(result['ok'], False)
        self.assertIs(result['timed_out'], False)


if __name__ == '__main__':
    unittest.main()
