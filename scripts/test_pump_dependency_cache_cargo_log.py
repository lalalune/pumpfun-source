#!/usr/bin/env python3
"""Exercise Cargo-log filtering through real dependency-cache publication.

The artifact bytes are synthetic; no compiler or native-build claim is made.
"""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'cargo_log_manifest_fixture', ROOT / 'tests/test_dependency_cache_manifest_state.py')
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
NOISE = ['123', 'true', 'null', '"stray"', '[1, 2]', 'not json at all']


@contextmanager
def finish_fixture(lines, *, direct=True):
    with tempfile.TemporaryDirectory(prefix='dep-cache-finish-') as directory:
        root = Path(directory)
        fixture = FIXTURE.DependencyCacheManifestStateTests()
        cache, target, log, report = fixture.cache_fixture(root)
        cache.package_id = 'pkg'
        cache.direct = direct
        if not direct:
            cache.record = {'main_command': None}
        log.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        yield cache, target, log, report


class CargoLogNonDictTests(unittest.TestCase):
    def test_non_object_json_lines_do_not_block_real_cache_publication(self):
        for noise in NOISE:
            with self.subTest(noise=noise), finish_fixture([noise]) as (cache, target, log, report):
                cache.finish(target, log, report)
                manifest = json.loads((cache.entry / 'MANIFEST.json').read_text())
                relative = 'release/deps/libdependency-0123456789abcdef.rlib'
                self.assertEqual(manifest['context'], cache.context)
                self.assertEqual((cache.entry / 'files' / relative).read_bytes(),
                                 (target / relative).read_bytes())
                self.assertEqual(cache.record['published_files'], 1)

    def test_real_artifact_rows_still_drive_compilation_accounting(self):
        artifacts = [
            {'reason': 'compiler-artifact', 'package_id': 'pkg', 'fresh': False},
            {'reason': 'compiler-artifact', 'package_id': 'external-fresh', 'fresh': True},
            {'reason': 'compiler-artifact', 'package_id': 'external-built', 'fresh': False},
            {'reason': 'build-finished', 'success': True},
        ]
        with finish_fixture([*NOISE, *map(json.dumps, artifacts)], direct=False) as (cache, target, log, report):
            cache.finish(target, log, report)
            self.assertTrue(cache.record['main_freshly_compiled'])
            self.assertEqual(cache.record['external_fresh'], 1)
            self.assertEqual(cache.record['external_rebuilt'], 1)
            self.assertTrue((cache.entry / 'MANIFEST.json').is_file())

    def test_noise_cannot_replace_a_missing_or_fresh_main_artifact(self):
        for extra in ([], [{'reason': 'compiler-artifact', 'package_id': 'pkg', 'fresh': True}]):
            with self.subTest(artifacts=extra), finish_fixture(
                    [*NOISE, *map(json.dumps, extra)], direct=False) as (cache, target, log, report):
                with self.assertRaisesRegex(AssertionError, 'main crate was not freshly compiled'):
                    cache.finish(target, log, report)
                self.assertFalse(cache.entry.exists())

    def test_malformed_artifact_objects_still_fail_before_publication(self):
        for artifact in ({'reason': 'compiler-artifact'},
                         {'reason': 'compiler-artifact', 'package_id': 'pkg'}):
            with self.subTest(artifact=artifact), finish_fixture(
                    [*NOISE, json.dumps(artifact)], direct=False) as (cache, target, log, report):
                with self.assertRaises(KeyError):
                    cache.finish(target, log, report)
                self.assertFalse(cache.entry.exists())


if __name__ == '__main__':
    unittest.main()
