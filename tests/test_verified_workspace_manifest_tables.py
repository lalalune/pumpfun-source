"""Verified-workspace splitting must preserve Cargo's interpretation of TOML."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import pump_build_verified as builder

PLAIN = '''[package]
name="pump-recovered"
version="0.1.0"
edition="2021"
[lib]
crate-type=["cdylib","lib"]
[profile.release]
panic="abort"
lto=false
codegen-units=1
[workspace]
'''
VARIANTS = [
    PLAIN,
    '# The [profile.release] settings are preserved below.\n' + PLAIN,
    PLAIN.replace('[lib]', 'description="""\n[profile.release]\nPackage text.\n[workspace]\n"""\n[lib]'),
    PLAIN + '# This workspace is intentionally empty.\n',
]
CARGO = (str(Path(os.environ['PUMP_TEST_RUST_BIN'])/'cargo')
         if os.environ.get('PUMP_TEST_RUST_BIN') else shutil.which('cargo'))


class WorkspaceManifestTests(unittest.TestCase):
    def test_package_and_release_meaning_survives_comments_and_multiline_values(self):
        for source in VARIANTS:
            with self.subTest(source=source):
                package, workspace = map(tomllib.loads, builder.workspace_manifests(source))
                original = tomllib.loads(source)
                self.assertEqual(package, {key: value for key, value in original.items()
                                           if key not in ('profile', 'workspace')})
                self.assertEqual(workspace['profile'], original['profile'])
                self.assertEqual(workspace['workspace'], {'members': ['programs/pump'], 'resolver': '2'})

    def test_current_program_staging_remains_byte_identical(self):
        text = (ROOT/'programs/pump/Cargo.toml').read_text()
        profile, workspace = text.index('[profile.release]'), text.index('[workspace]')
        previous = (text[:profile].rstrip()+'\n',
                    '[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n'+text[profile:workspace].strip()+'\n')
        self.assertEqual(builder.workspace_manifests(text), previous)

    def test_unsupported_layouts_remain_rejected(self):
        for source in (PLAIN+'members=[]\n', PLAIN+'[profile.dev]\nopt-level=0\n',
                       PLAIN.replace('[profile.release]', '[workspace]\n[profile.release]').rsplit('[workspace]', 1)[0],
                       PLAIN+'[package.metadata]\nextra=true\n'):
            with self.subTest(source=source), self.assertRaises((AssertionError, tomllib.TOMLDecodeError)):
                builder.workspace_manifests(source)

    @unittest.skipUnless(CARGO, 'Cargo is required for actual manifest admission')
    def test_cargo_accepts_each_original_and_staged_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, text in enumerate(VARIANTS):
                source = root/str(index)
                (source/'src').mkdir(parents=True)
                (source/'Cargo.toml').write_text(text)
                (source/'src/lib.rs').write_text('pub fn value()->u64{27}\n')
                original = subprocess.run([CARGO, 'metadata', '--offline', '--no-deps', '--format-version=1'],
                                          cwd=source, capture_output=True, text=True, timeout=20)
                self.assertEqual(original.returncode, 0, original.stderr)
                package, workspace = builder.workspace_manifests(text)
                stage = root/(str(index)+'-staged')
                crate = stage/'programs/pump'
                (crate/'src').mkdir(parents=True)
                (crate/'src/lib.rs').write_bytes((source/'src/lib.rs').read_bytes())
                (crate/'Cargo.toml').write_text(package)
                (stage/'Cargo.toml').write_text(workspace)
                staged = subprocess.run([CARGO, 'metadata', '--offline', '--no-deps', '--format-version=1'],
                                        cwd=stage, capture_output=True, text=True, timeout=20)
                self.assertEqual(staged.returncode, 0, staged.stderr)
                for key in ('name', 'version', 'description', 'edition'):
                    self.assertEqual(json.loads(original.stdout)['packages'][0][key],
                                     json.loads(staged.stdout)['packages'][0][key])

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_BUILD_TEST_SDK'),
                         'set PUMP_BUILD_TEST_SDK to an authenticated v1.44 macOS SDK')
    def test_actual_verified_sbf_builds_preserve_equal_program_output(self):
        probe = ROOT/'research/verified-workspace-manifest-tables-20261101/probe.py'
        result = subprocess.run([sys.executable, '-B', str(probe), str(ROOT), os.environ['PUMP_BUILD_TEST_SDK']],
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        self.assertEqual(len(records), 4)
        for record in records.values():
            self.assertEqual(record['returncode'], 0, record)
            self.assertTrue(record['source_unchanged'])
            self.assertEqual(record['candidate_sha256'], records['plain']['candidate_sha256'])


if __name__ == '__main__':
    unittest.main()
