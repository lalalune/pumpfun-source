"""Keep configured reconstruction caches stable across Cargo's working directory."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MODULES = {
    'fastbuild': HERE / 'fastbuild.py',
    'bootstrap': HERE.parent / 'toolchain/bootstrap.py',
}


def load(name, cache=None):
    with patch.dict(os.environ, {'PUMP_BUILD_SLOTS': '1'}, clear=True):
        if cache is not None:
            os.environ['PUMP_RECON_HOME'] = str(cache)
        spec = importlib.util.spec_from_file_location('_cache_test_' + name, MODULES[name])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class CachePaths(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pump-cache-paths-')
        self.addCleanup(temporary.cleanup)
        self.addCleanup(os.chdir, Path.cwd())
        self.root = Path(temporary.name).resolve()
        self.invocation = self.root / 'invocation'
        self.invocation.mkdir()
        os.chdir(self.invocation)

    def assert_roots(self, builder, bootstrap, expected):
        self.assertEqual(builder.CACHE, expected)
        self.assertEqual(bootstrap.HOME_CACHE, expected)
        self.assertEqual(builder.LOCKDIR, expected / 'locks')
        self.assertEqual(bootstrap.HYBRID, expected / 'toolchains/hybrid144')
        self.assertEqual(builder.RECIPES['identity']['rustc'], bootstrap.HYBRID / 'rust/bin/rustc')
        self.assertEqual(builder.RECIPES['identity']['template'], expected / 'template-target-sbpf')
        self.assertEqual(builder.RECIPES['mac']['template'], expected / 'template-target')

    def test_relative_cache_remains_bound_after_chdir(self):
        builder, bootstrap = load('fastbuild', 'cache with spaces'), load('bootstrap', 'cache with spaces')
        workspace = self.invocation / 'lane/work/ws'
        workspace.mkdir(parents=True)
        os.chdir(workspace)
        self.assert_roots(builder, bootstrap, self.invocation / 'cache with spaces')

    def test_absolute_cache_is_unchanged(self):
        cache = self.root / 'absolute cache'
        self.assert_roots(load('fastbuild', cache), load('bootstrap', cache), cache)

    def test_default_cache_is_unchanged(self):
        self.assert_roots(load('fastbuild'), load('bootstrap'), Path.home() / '.cache/pumpfun-reconstruction')

    def test_symlink_and_parent_components_keep_their_spelling(self):
        storage = self.root / 'storage/nested'
        storage.mkdir(parents=True)
        link = self.invocation / 'cache link'
        link.symlink_to(storage, target_is_directory=True)
        for cache in (Path('cache link'), link, Path('cache link/../sibling')):
            with self.subTest(cache=cache):
                expected = self.invocation / cache
                self.assert_roots(load('fastbuild', cache), load('bootstrap', cache), expected)

    def test_real_offline_cargo_from_staged_workspace(self):
        cargo, rustc = shutil.which('cargo'), shutil.which('rustc')
        if not cargo or not rustc:
            self.skipTest('host Cargo and rustc are needed for the offline compiler-path regression')
        builder = load('fastbuild', 'cache with spaces')
        configured = builder.RECIPES['identity']['rustc']
        compiler = self.invocation / configured
        compiler.parent.mkdir(parents=True)
        compiler.symlink_to(rustc)
        workspace = self.invocation / 'lane/work/ws'
        (workspace / 'src').mkdir(parents=True)
        # Compile unchanged, dependency-free repository source; keep Cargo's state isolated.
        for relative in ('Cargo.toml', 'src/lib.rs'):
            shutil.copyfile(ROOT / 'crates/native-transfer-fee' / relative, workspace / relative)
        env = {
            'PATH': os.pathsep.join((os.defpath, str(Path(cargo).parent), str(Path(rustc).parent))),
            'CARGO_HOME': str(self.root / 'cargo-home'),
            'CARGO_TARGET_DIR': str(self.root / 'target'),
            'RUSTC': str(configured),
            'RUSTC_WRAPPER': '',
            'RUSTC_WORKSPACE_WRAPPER': '',
        }
        result = subprocess.run([cargo, 'check', '--offline', '--quiet'], cwd=workspace,
                                env=env, capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
