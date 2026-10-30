"""Real concurrent SBF builds must not mix a binary with another source receipt."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import fastbuild


class OutputLockTests(unittest.TestCase):
    def test_distinct_workspaces_cannot_publish_through_one_output_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            alias = root / 'alias'
            alias.symlink_to(output, target_is_directory=True)
            with fastbuild.output_lock(output), patch.object(fastbuild, '_build_locked') as trial:
                with self.assertRaisesRegex(RuntimeError, 'output already in use'):
                    fastbuild.build(root / 'source', root / 'other-work', alias)
                trial.assert_not_called()

    def test_other_outputs_are_independent_and_failure_releases_the_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'output'
            with self.assertRaisesRegex(ValueError, 'trial failed'):
                with fastbuild.output_lock(output), fastbuild.output_lock(root / 'other-output'):
                    raise ValueError('trial failed')
            lock = root / '.output.fastbuild-output.lock'
            inode = lock.stat().st_ino
            with fastbuild.output_lock(output):
                self.assertEqual(lock.stat().st_ino, inode)


@unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit macOS v1.44 SDK')
class OutputRaceTests(unittest.TestCase):
    def exercise(self, shared):
        with tempfile.TemporaryDirectory(prefix='pump-output-race-') as temporary:
            root = Path(temporary).resolve()
            sources = []
            for value in (17, 29):
                source = root / f'source-{value}'
                (source / 'src').mkdir(parents=True)
                (source / 'Cargo.toml').write_text(
                    '[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
                    '[lib]\ncrate-type=["cdylib"]\n'
                    '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')
                (source / 'Cargo.lock').write_text(
                    'version=3\n[[package]]\nname="pump-recovered"\nversion="0.1.0"\n')
                (source / 'src/lib.rs').write_text(
                    '#![no_std]\n#[no_mangle] pub extern "C" fn entrypoint(_: *mut u8)->u64 { '
                    + str(value) + ' }\n'
                    '#[panic_handler] fn panic(_: &core::panic::PanicInfo)->! { loop {} }\n')
                sources.append(source)
            work_a, work_b = root / 'work-a', root / 'work-b'
            out_a = root / 'output-a'
            out_b = out_a if shared else root / 'output-b'
            sdk = Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve()
            recipe = {'triple': 'sbf-solana-solana', 'rustc': sdk / 'rust/bin/rustc',
                      'template': root / 'no-template'}
            ready, release = threading.Event(), threading.Event()
            real = fastbuild.run_compiler

            def delayed(command, **kwargs):
                result = real(command, **kwargs)
                if Path(kwargs['cwd']).resolve() == (work_a / 'ws').resolve():
                    ready.set()
                    if not release.wait(30):
                        raise RuntimeError('test publication barrier timed out')
                return result

            def build(source, work, output):
                return fastbuild.build(source, work, output, recipe='identity', quiet=True)

            with patch.object(fastbuild, 'SDK', sdk), \
                 patch.dict(fastbuild.RECIPES, {'identity': recipe}), \
                 patch.object(fastbuild, 'LOCKDIR', root / 'locks'), \
                 patch.object(Path, 'home', return_value=root / 'home'), \
                 patch.object(fastbuild, 'run_compiler', delayed), ThreadPoolExecutor(1) as pool:
                first = pool.submit(build, sources[0], work_a, out_a)
                blocked, second = None, None
                try:
                    if not ready.wait(30):
                        if first.done():
                            first.result()  # Surface a failed build instead of masking it as a barrier timeout.
                        self.fail('first build did not reach the publication barrier')
                    try:
                        second = build(sources[1], work_b, out_b)
                    except RuntimeError as error:
                        blocked = error
                finally:
                    release.set()
                result = first.result(timeout=30)
                self.assertTrue(result['ok'])
                receipt = json.loads((out_a / 'source-inputs.json').read_text())
                self.assertEqual(receipt['sha256'], result['source_sha256'],
                                 'published ELF and source receipt came from different real builds')
                self.assertEqual(hashlib.sha256((out_a / 'unstripped.so').read_bytes()).hexdigest(),
                                 result['unstripped_sha256'])
                if shared:
                    self.assertIsNotNone(blocked)
                    self.assertIn('output already in use', str(blocked))
                    # Releasing the first build must permit a normal retry.
                    retry = build(sources[1], work_b, out_b)
                    self.assertTrue(retry['ok'])
                    self.assertNotEqual(retry['unstripped_sha256'], result['unstripped_sha256'])
                    self.assertEqual(json.loads((out_b / 'source-inputs.json').read_text())['sha256'],
                                     retry['source_sha256'])
                else:
                    self.assertIsNone(blocked)
                    self.assertTrue(second['ok'])
                    self.assertNotEqual(second['unstripped_sha256'], result['unstripped_sha256'])

    def test_shared_output_cannot_mix_receipts_and_binaries(self):
        self.exercise(shared=True)

    def test_disjoint_outputs_can_build_independently(self):
        self.exercise(shared=False)


if __name__ == '__main__':
    unittest.main()
