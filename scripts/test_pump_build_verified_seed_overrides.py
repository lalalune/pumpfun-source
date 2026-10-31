#!/usr/bin/env python3
"""A dependency-cache seed must share the compiler overrides of the cache key."""

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_build_verified as build  # noqa: E402

OVERRIDE = {'CARGO_PROFILE_RELEASE_OPT_LEVEL': '0'}


class StopBuild(Exception):
    pass


class SeedOverrides(unittest.TestCase):
    def run_main(self, root, overrides, *arguments):
        sdk = root / 'sdk'
        for name in ['rust/bin/rustc', 'rust/bin/cargo', 'llvm/bin/llvm-objcopy']:
            (sdk / name).parent.mkdir(parents=True, exist_ok=True)
            (sdk / name).write_bytes(b'tool')
        cache = mock.MagicMock()
        cache.entry.exists.return_value = False
        cache.record = {'status': 'miss'}
        argv = ['pump_build_verified.py', '--sdk', str(sdk), '--registry-home', str(root / 'home'),
                '--output', str(root / 'out'), *arguments]
        ambient = {k: v for k, v in os.environ.items()
                   if k != 'RUSTC_BOOTSTRAP' and not k.startswith('CARGO_PROFILE_')}
        with mock.patch.object(sys, 'argv', argv), \
                mock.patch.dict(os.environ, {**ambient, **overrides}, clear=True), \
                mock.patch.object(build, 'DependencyCache', return_value=cache), \
                mock.patch.object(build, 'source_manifest', return_value={}), \
                mock.patch.object(build.pump_target_library_profile, 'inventory', return_value={'lib': 'hash'}), \
                mock.patch.object(build.subprocess, 'run', side_effect=StopBuild):
            try:
                build.main()
            except StopBuild:
                return cache, None
            except AssertionError as error:
                return cache, str(error)
        return cache, None

    def seeded(self, root, seed_environment, overrides):
        seed = root / 'seed'
        seed.mkdir()
        (seed / 'build-comparison.json').write_text(
            json.dumps({'environment': seed_environment}), encoding='utf-8')
        return self.run_main(root, overrides, '--dependency-cache', str(root / 'cache'),
                             '--dependency-cache-seed', str(seed))

    def test_receipt_records_overrides(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.run_main(root, {**OVERRIDE, 'RUSTC_BOOTSTRAP': '1'})
            environment = json.loads((root / 'out/build-attempt.json').read_text(encoding='utf-8'))['environment']
        self.assertEqual(environment.get('CARGO_PROFILE_RELEASE_OPT_LEVEL'), '0')
        self.assertEqual(environment.get('RUSTC_BOOTSTRAP'), '1')

    def test_differing_seed_is_refused_before_import(self):
        for seed_environment, overrides in [(OVERRIDE, {}), ({}, OVERRIDE),
                                            (OVERRIDE, {'CARGO_PROFILE_RELEASE_OPT_LEVEL': 's'})]:
            with self.subTest(seed=seed_environment, current=overrides), \
                    tempfile.TemporaryDirectory() as directory:
                cache, error = self.seeded(Path(directory), seed_environment, overrides)
                self.assertEqual(error, 'seed compiler overrides differ')
                cache.import_clean_build.assert_not_called()

    def test_matching_seed_is_imported(self):
        for overrides in [{}, OVERRIDE]:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as directory:
                cache, error = self.seeded(Path(directory), overrides, overrides)
                self.assertIsNone(error)
                cache.import_clean_build.assert_called_once()


if __name__ == '__main__':
    unittest.main()
