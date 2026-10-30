"""Build and retain real link evidence when --work and --out name one folder."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import fastbuild
from source_inputs import snapshot


@unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
class SharedOutputTests(unittest.TestCase):
    files = ('unstripped.so', 'candidate.so', 'build.log', 'source-inputs.json',
             'link-receipt.json', 'link.map')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pump-shared-output-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        (self.source / 'src').mkdir(parents=True)
        (self.source / 'Cargo.toml').write_text(
            '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
            '[lib]\ncrate-type=["cdylib"]\n'
            '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
        (self.source / 'Cargo.lock').write_text(
            'version=3\n[[package]]\nname="pump-recovered"\nversion="0.1.0"\n')
        (self.source / 'src/lib.rs').write_text(
            '#![no_std]\n#[no_mangle] pub extern "C" fn entrypoint(_: *mut u8)->u64 { 0 }\n'
            '#[panic_handler] fn panic(_: &core::panic::PanicInfo)->! { loop {} }\n')
        (self.source / 'link').mkdir()
        shutil.copy2(Path(fastbuild.__file__).with_name('sbf_default.ld'), self.source / 'link/ordered.ld')
        sdk = Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve()
        recipe = {'triple': 'sbf-solana-solana', 'rustc': sdk / 'rust/bin/rustc',
                  'template': self.root / 'no-template'}
        self.enterContext(patch.object(fastbuild, 'SDK', sdk))
        self.enterContext(patch.dict(fastbuild.RECIPES, {'identity': recipe}))
        self.enterContext(patch.object(fastbuild, 'LOCKDIR', self.root / 'locks'))
        self.enterContext(patch.object(Path, 'home', return_value=self.root / 'home'))
        self.work = self.root / 'work'

    def build(self, work, output):
        return fastbuild.build(self.source, work, output, recipe='identity', quiet=True)

    def saved(self, output):
        return {name: (output / name).read_bytes() for name in self.files}

    def seed_previous_real_build(self):
        output = self.root / 'control-output'
        self.assertTrue(self.build(self.root / 'control-work', output)['ok'])
        self.work.mkdir()
        for name in self.files:
            shutil.copy2(output / name, self.work / name)
        return self.saved(self.work)

    def assert_archived(self, previous):
        archives = list((self.work / 'previous').iterdir())
        self.assertTrue(any(all((a / n).is_file() and (a / n).read_bytes() == data
                                for n, data in previous.items()) for a in archives),
                        'prior binary/log/source/link evidence was not retained together')

    def test_shared_output_finishes_real_link_and_publication(self):
        before = snapshot(self.source)
        result = self.build(self.work, self.work)
        self.assertTrue(result['ok'])
        self.assertTrue((self.work / 'unstripped.so').read_bytes().startswith(b'\x7fELF'))
        self.assertEqual(set(self.saved(self.work)), set(self.files))
        self.assertEqual(snapshot(self.source), before)

    def test_successive_rebuilds_keep_complete_prior_link_evidence(self):
        previous = self.seed_previous_real_build()
        self.assertTrue(self.build(self.work, self.work)['ok'])
        self.assert_archived(previous)
        previous = self.saved(self.work)
        self.assertTrue(self.build(self.work, self.work)['ok'])
        self.assert_archived(previous)
        self.assertEqual(len(list((self.work / 'previous').iterdir())), 2)

    def test_failed_rebuild_preserves_old_receipt_and_map(self):
        previous = self.seed_previous_real_build()
        (self.source / 'src/lib.rs').write_text('compile_error!("expected failure");\n')
        self.assertFalse(self.build(self.work, self.work)['ok'])
        self.assert_archived(previous)
        for name in ('unstripped.so', 'candidate.so', 'link-receipt.json', 'link.map'):
            self.assertFalse((self.work / name).exists())


if __name__ == '__main__':
    unittest.main()
