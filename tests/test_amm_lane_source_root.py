"""An established AMM lane must refuse a source root it will not build."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_amm_source_root', ROOT / 'scripts/amm_sell/native_build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


@unittest.skipUnless(shutil.which('rsync'), 'the actual POSIX staging workflow requires rsync')
class LaneSourceRootTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='amm-lane-source-root-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'selected-repo'
        for name in ('programs/pump-amm', 'crates/native-transfer-fee'):
            shutil.copytree(ROOT / name, self.source / name)
        self.lane = self.root / 'lane'
        for name in ('SDK', 'CARGO_HOME', 'SEED_TARGET', 'PRISTINE'):
            self.addCleanup(setattr, native, name, getattr(native, name))
        native.SDK = self.root / 'intentionally-missing-sdk'
        native.CARGO_HOME = self.root / 'cargo-home'
        native.SEED_TARGET = self.root / 'absent-warm-target'
        native.PRISTINE = self.root / 'no-global-pristine'

    def stage_until_compiler_boundary(self, identifier, **kwargs):
        # An absent SDK stops at the compiler subprocess; nothing is simulated.
        with self.assertRaises(FileNotFoundError):
            native.build(self.lane, identifier, **kwargs)

    def test_other_source_root_is_refused_on_an_established_lane(self):
        self.stage_until_compiler_boundary('first', source_root=self.source)
        other = self.root / 'other-repo'
        shutil.copytree(self.source, other)
        sell = other / native.SELL_REL
        sell.write_bytes(sell.read_bytes() + b'\n// a different selected source\n')
        before = native.recipe.file_inventory(self.lane / 'ws')
        try:
            native.build(self.lane, 'second', source_root=other)
        except FileNotFoundError:
            self.fail('the lane reached the compiler on its old baseline, not the requested source root')
        except RuntimeError as error:
            self.assertIn('workspace input changed', str(error))
        self.assertEqual(native.recipe.file_inventory(self.lane / 'ws'), before)
        self.assertFalse((self.lane / 'out/second').exists())

    def test_same_source_root_still_reaches_the_compiler(self):
        self.stage_until_compiler_boundary('first', source_root=self.source)
        self.stage_until_compiler_boundary('second', source_root=self.source)
        self.assertTrue((self.lane / 'out/second/sell.rs').is_file())


if __name__ == '__main__':
    unittest.main()
