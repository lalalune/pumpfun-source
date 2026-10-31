"""The AMM recipe must own the root compiler wrapper, including Cargo aliases."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('amm_environment', ROOT / 'scripts/amm_sell/native_build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
HOST_TOOLS = (Path(os.environ['PUMP_TEST_RUST_BIN']) if os.environ.get('PUMP_TEST_RUST_BIN')
              else Path(shutil.which('rustc')).parent if shutil.which('rustc') else None)


class BuildEnvironmentTests(unittest.TestCase):
    def test_both_workspace_wrapper_spellings_are_removed(self):
        with patch.dict(os.environ, {'RUSTC_WORKSPACE_WRAPPER': '/ambient/one',
                                     'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER': '/ambient/two'}):
            env = native.build_environment(Path('/harness'), Path('/target'), Path('/out'), '', 1, None)
        self.assertNotIn('RUSTC_WORKSPACE_WRAPPER', env)
        self.assertNotIn('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', env)
        self.assertEqual(env['RUSTC_WRAPPER'], str(Path('/harness') / 'rustc_wrapper.py'))

    def test_ambient_cargo_overrides_do_not_reach_the_recipe(self):
        overrides = {
            'CARGO_TARGET_SBPF_SOLANA_SOLANA_LINKER': '/absent/linker',
            'CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER': '/absent/host-linker',
            'CARGO_PROFILE_RELEASE_LTO': 'true',
            'CARGO_PROFILE_RELEASE_OPT_LEVEL': '1',
            'CARGO_PROFILE_RELEASE_CODEGEN_UNITS': '16',
            'CARGO_INCREMENTAL': 'true',
            'CARGO_BUILD_INCREMENTAL': 'true',
        }
        for name, value in overrides.items():
            with self.subTest(name=name), patch.dict(os.environ, {name: value}):
                env = native.build_environment(Path('/harness'), Path('/target'), Path('/out'), '', 1, None)
            self.assertNotIn(name, env, name + ' reached the pinned recipe')
        with patch.dict(os.environ, overrides):
            env = native.build_environment(Path('/harness'), Path('/target'), Path('/out'), '', 1, None)
        self.assertEqual(env['CARGO_BUILD_JOBS'], '1')
        self.assertEqual(env['RUSTC_WRAPPER'], str(Path('/harness') / 'rustc_wrapper.py'))
        self.assertIn('CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS', env)

    @unittest.skipUnless(os.name != 'nt' and HOST_TOOLS and (HOST_TOOLS / 'cargo').is_file(),
                         'requires host Cargo/rustc on PATH or PUMP_TEST_RUST_BIN')
    def test_real_cargo_does_not_nest_an_ambient_workspace_wrapper(self):
        tools = HOST_TOOLS.resolve()
        with tempfile.TemporaryDirectory(prefix='amm-build-env-') as folder:
            root = Path(folder)
            crate = root / 'crate'; (crate / 'src').mkdir(parents=True)
            (crate / 'Cargo.toml').write_text('[package]\nname="probe"\nversion="0.1.0"\nedition="2021"\n[workspace]\n')
            (crate / 'src/main.rs').write_text('#![allow(unexpected_cfgs)]\nfn main(){println!("{}",cfg!(ambient_override));}\n')
            harness = root / 'harness'; harness.mkdir()
            root_wrapper = harness / 'rustc_wrapper.py'
            root_wrapper.write_text(native.RUSTC_WRAPPER)
            root_wrapper.chmod(0o755)
            ambient = root / 'ambient.py'
            ambient.write_text('#!' + sys.executable + '\nimport os,sys\n'
                               'compiler,*args=sys.argv[1:]\n'
                               'if "--crate-name" in args: args += ["--cfg", "ambient_override"]\n'
                               'os.execv(compiler,[compiler,*args])\n')
            ambient.chmod(0o755)
            sdk = root / 'sdk'; (sdk / 'rust/bin').mkdir(parents=True)
            for name in ('rustc', 'rustdoc'):
                (sdk / 'rust/bin' / name).symlink_to(tools / name)
            for spelling in ('RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'):
                with self.subTest(spelling=spelling), patch.dict(os.environ, {spelling: str(ambient)}), \
                        patch.object(native, 'SDK', sdk), patch.object(native, 'CARGO_HOME', root / 'cargo-home'):
                    target = root / spelling
                    env = native.build_environment(harness, target, root, '', 1, None)
                    result = subprocess.run([str(tools / 'cargo'), 'build', '--release', '--offline'],
                                            cwd=crate, env=env, capture_output=True, text=True, timeout=45)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    actual = subprocess.check_output([str(target / 'release/probe')], text=True).strip()
                    self.assertEqual(actual, 'false', 'ambient wrapper changed the compiled program')


if __name__ == '__main__':
    unittest.main()
