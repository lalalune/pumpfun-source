"""Exercise native AMM source selection with real staged Rust and POSIX rsync."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_amm_baseline', ROOT / 'scripts/amm_sell/native_build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


@unittest.skipUnless(shutil.which('rsync'), 'the actual POSIX staging workflow requires rsync')
class LaneBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='amm-lane-baseline-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'selected-repo'
        for name in ('programs/pump-amm', 'crates/native-transfer-fee'):
            shutil.copytree(ROOT / name, self.source / name)
        self.selected = self.source / native.SELL_REL
        self.selected.write_bytes(self.selected.read_bytes() + b'\n// explicitly selected source baseline\n')
        self.pristine = self.root / 'canonical-pristine'
        native.recipe.stage(ROOT, self.pristine)
        self.lane = self.root / 'lane'
        for name in ('SDK', 'CARGO_HOME', 'SEED_TARGET', 'PRISTINE'):
            self.addCleanup(setattr, native, name, getattr(native, name))
        native.SDK = self.root / 'intentionally-missing-sdk'
        native.CARGO_HOME = self.root / 'cargo-home'
        native.SEED_TARGET = self.root / 'absent-warm-target'
        native.PRISTINE = self.pristine

    def stage_until_compiler_boundary(self, identifier, **kwargs):
        # Run the real recipe and rsync. An absent SDK stops exactly at the
        # compiler subprocess; no compiler or build success is simulated.
        with self.assertRaises(FileNotFoundError):
            native.build(self.lane, identifier, **kwargs)

    def test_explicit_root_survives_available_global_pristine(self):
        self.stage_until_compiler_boundary('selected', source_root=self.source)
        self.assertEqual((self.lane / 'ws' / native.SELL_REL).read_bytes(), self.selected.read_bytes())
        self.assertTrue(native.recipe.verify_workspace(self.source, self.lane / 'ws')['verified'])
        self.assertEqual((self.lane / 'out/selected/sell.rs').read_bytes(), self.selected.read_bytes())

    def test_later_attempt_keeps_the_same_selected_baseline(self):
        self.stage_until_compiler_boundary('first', source_root=self.source)
        replacement = self.root / 'first-attempt.rs'
        replacement.write_bytes(self.selected.read_bytes() + b'// attempt-only change\n')
        self.stage_until_compiler_boundary('patched', sell=replacement)
        self.assertEqual((self.lane / 'ws' / native.SELL_REL).read_bytes(), replacement.read_bytes())
        self.stage_until_compiler_boundary('reset')
        self.assertEqual((self.lane / 'ws' / native.SELL_REL).read_bytes(), self.selected.read_bytes())
        self.assertTrue(native.recipe.verify_workspace(self.source, self.lane / 'ws')['verified'])

    def test_attempt_changes_do_not_leak_without_global_pristine(self):
        native.PRISTINE = self.root / 'no-global-pristine'
        replacement = self.root / 'replacement.rs'
        replacement.write_bytes(self.selected.read_bytes() + b'// first attempt only\n')
        self.stage_until_compiler_boundary('first', source_root=self.source, sell=replacement)
        self.stage_until_compiler_boundary('second')
        self.assertEqual((self.lane / 'ws' / native.SELL_REL).read_bytes(), self.selected.read_bytes())
        self.assertTrue(native.recipe.verify_workspace(self.source, self.lane / 'ws')['verified'])

    def test_default_canonical_source_is_a_positive_control(self):
        self.stage_until_compiler_boundary('canonical')
        self.assertTrue(native.recipe.verify_workspace(ROOT, self.lane / 'ws')['verified'])

    def test_unknown_legacy_baseline_preserves_existing_workspace(self):
        native.PRISTINE = self.root / 'missing-pristine'
        native.recipe.stage(self.source, self.lane / 'ws')
        sell = self.lane / 'ws' / native.SELL_REL
        sell.write_bytes(sell.read_bytes() + b'// legacy attempt with unknown origin\n')
        before = native.recipe.file_inventory(self.lane / 'ws')
        with self.assertRaisesRegex(SystemExit, 'establish its baseline'):
            native.build(self.lane, 'legacy')
        self.assertEqual(native.recipe.file_inventory(self.lane / 'ws'), before)
        self.assertFalse((self.lane / 'baseline-ws').exists())


if __name__ == '__main__':
    unittest.main()
