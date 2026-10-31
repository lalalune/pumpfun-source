"""A rejected AMM lane patch must leave its reason in the retained attempt log."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_amm_patch_log', ROOT / 'scripts/amm_sell/native_build.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


@unittest.skipUnless(shutil.which('rsync') and shutil.which('patch'), 'the staging workflow needs rsync and patch')
class LanePatchLogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='amm-lane-patch-log-')
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

    def diff(self, before, after):
        return (f'--- a/{native.SELL_REL}\n+++ b/{native.SELL_REL}\n'
                f'@@ -1 +1 @@\n-{before}\n+{after}\n').encode()

    def test_rejected_patch_keeps_its_hunk_message(self):
        change = self.root / 'rejected.diff'
        change.write_bytes(self.diff('a line this source does not contain', 'replacement'))
        with self.assertRaises(subprocess.CalledProcessError):
            native.build(self.lane, 'rejected', source_root=self.source, patch=change)
        log = self.lane / 'out/rejected/build.log'
        self.assertTrue(log.is_file(), 'the failed attempt kept no log of the rejected patch')
        self.assertIn('hunk', log.read_text().lower())
        self.assertIn('failed', log.read_text().lower())

    def test_applied_patch_still_reaches_the_compiler(self):
        sell = self.source / native.SELL_REL
        first = sell.read_text().splitlines()[0]
        change = self.root / 'applied.diff'
        change.write_bytes(self.diff(first, first + ' // patched'))
        with self.assertRaises(FileNotFoundError):
            native.build(self.lane, 'applied', source_root=self.source, patch=change)
        self.assertIn('// patched', (self.lane / 'ws' / native.SELL_REL).read_text())


if __name__ == '__main__':
    unittest.main()
