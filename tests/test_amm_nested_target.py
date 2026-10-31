"""Rust source directories named target are not Cargo output directories."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/amm_sell'))
import native_build
import workspace_recipe
import test_workspace_recipe_staging as staging_tests
HOST_TOOLS = (Path(os.environ['PUMP_TEST_RUST_BIN']) if os.environ.get('PUMP_TEST_RUST_BIN')
              else Path(shutil.which('rustc')).parent if shutil.which('rustc') else None)


class NestedTargetTests(unittest.TestCase):
    def setUp(self):
        self.fixture = staging_tests.SourceContainmentTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root, self.source = self.fixture.root, self.fixture.source

    def module(self, crate):
        relative = crate + '/src/target/mod.rs'
        path = self.source / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b'pub fn answer() -> u8 { 7 }\n')
        (self.source / crate / 'src/lib.rs').write_bytes(b'mod target;\npub fn answer() -> u8 {target::answer()}\n')
        return relative

    def test_source_and_workspace_receipts_include_nested_target_modules(self):
        paths = [self.module(crate) for crate in staging_tests.MEMBERS]
        staged = self.root / 'stage'
        report = workspace_recipe.stage(self.source, staged)
        for relative in paths:
            self.assertEqual((staged / relative).read_bytes(), (self.source / relative).read_bytes())
            self.assertIn(relative, report['input_sha256'])
            self.assertIn(relative, report['workspace_sha256'])
        (staged / paths[0]).write_bytes(b'pub fn answer() -> u8 { 8 }\n')
        with self.assertRaises(RuntimeError):
            workspace_recipe.verify_workspace(self.source, staged)

    def test_generated_main_crate_target_still_stays_out_of_the_stage(self):
        generated = self.source / 'programs/pump-amm/target/generated.rs'
        generated.parent.mkdir(); generated.write_bytes(b'not source')
        staged = self.root / 'stage'
        workspace_recipe.stage(self.source, staged)
        self.assertFalse((staged / generated.relative_to(self.source)).exists())

    def test_vendor_crate_root_target_is_excluded_but_nested_source_is_retained(self):
        vendor = self.source / 'programs/pump-amm/vendor/solana-pubkey'
        generated = vendor / 'target/generated.rs'
        source = vendor / 'src/target/mod.rs'
        for path in (generated, source):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'// vendor fixture\n')
        staged = self.root / 'stage'
        report = workspace_recipe.stage(self.source, staged)
        self.assertFalse((staged / generated.relative_to(self.source)).exists())
        relative = source.relative_to(self.source).as_posix()
        self.assertEqual((staged / relative).read_bytes(), source.read_bytes())
        self.assertIn(relative, report['input_sha256'])

    @unittest.skipUnless(HOST_TOOLS and (HOST_TOOLS / 'cargo').is_file(), 'requires host Cargo/rustc')
    def test_real_cargo_builds_the_same_source_before_and_after_staging(self):
        self.module('programs/pump-amm')
        tools = HOST_TOOLS.resolve()
        env = dict(os.environ, CARGO_HOME=str(self.root / 'cargo-home'), RUSTC=str(tools / 'rustc'))
        for name in ('RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'):
            env.pop(name, None)
        source_manifest = self.source / 'programs/pump-amm/Cargo.toml'
        result = subprocess.run([str(tools / 'cargo'), 'generate-lockfile', '--offline',
                                 '--manifest-path', str(source_manifest)],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        staged = self.root / 'stage'
        workspace_recipe.stage(self.source, staged)
        for name, manifest in [('original', source_manifest), ('staged', staged / 'Cargo.toml')]:
            with self.subTest(workspace=name):
                result = subprocess.run([str(tools / 'cargo'), 'build', '--offline', '--locked', '--release',
                                         '--manifest-path', str(manifest), '--target-dir', str(self.root / name)],
                                        cwd=self.root, env=env, capture_output=True, text=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('rsync'), 'requires the real POSIX staging workflow')
    def test_lane_reset_restores_nested_target_and_removes_attempt_only_files(self):
        relative = self.module('programs/pump-amm')
        # A selected pristine workspace can already contain this valid module.
        pristine = self.root / 'pristine'
        workspace_recipe.stage(self.source, pristine)
        # Keep this reset test independent of the input-inventory defect.
        nested = pristine / relative
        nested.parent.mkdir(parents=True, exist_ok=True)
        nested.write_bytes((self.source / relative).read_bytes())
        sell = pristine / native_build.SELL_REL
        sell.parent.mkdir(parents=True, exist_ok=True); sell.write_bytes(b'// synthetic sell\n')
        for name, value in [('PRISTINE', pristine), ('SDK', self.root / 'absent-sdk'),
                            ('SEED_TARGET', self.root / 'absent-seed')]:
            previous = getattr(native_build, name)
            self.addCleanup(setattr, native_build, name, previous)
            setattr(native_build, name, value)
        lane = self.root / 'lane'
        for attempt in ('first', 'reset'):
            if attempt == 'reset':
                (lane / 'ws' / relative).write_bytes(b'pub fn answer() -> u8 { 9 }\n')
                (lane / 'ws' / relative).with_name('attempt-only.rs').write_bytes(b'// attempt\n')
            with self.assertRaises(FileNotFoundError):
                native_build.build(lane, attempt)
        self.assertEqual((lane / 'ws' / relative).read_bytes(), nested.read_bytes())
        self.assertFalse((lane / 'ws' / relative).with_name('attempt-only.rs').exists())


if __name__ == '__main__':
    unittest.main()
