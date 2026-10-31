"""Regression tests for path confinement in scripts/pump_dependency_cache.py."""

import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import pump_dependency_cache as cache_mod


class DependencyCachePathConfinementTests(unittest.TestCase):
    def _make_cache(self, base):
        repo = (base / 'repo').resolve()
        crate = repo / 'programs/pump'
        crate.mkdir(parents=True, exist_ok=True)
        (crate / 'Cargo.toml').write_text('[package]\nname = "pump"\nversion = "0.1.0"\n', encoding='utf-8')
        sdk = (base / 'sdk').resolve()
        (sdk / 'rust/bin').mkdir(parents=True, exist_ok=True)
        rustc = sdk / 'rust/bin/rustc'
        cargo = sdk / 'rust/bin/cargo'
        rustc.write_text('#!/bin/sh\n', encoding='utf-8')
        cargo.write_text('#!/bin/sh\n', encoding='utf-8')
        wrapper = repo / 'wrapper.py'
        wrapper.write_text('#!/usr/bin/env python3\n', encoding='utf-8')

        cache = object.__new__(cache_mod.DependencyCache)
        cache.sdk = sdk
        cache.target = 'sbf-solana-solana'
        cache.target_flags_key = 'CARGO_TARGET_SBF_SOLANA_SOLANA_RUSTFLAGS'
        cache.direct = True
        cache.root = (base / 'cache').resolve()
        cache.repo = repo
        cache.crate = crate
        cache.workspace = repo
        cache.env = {
            'RUSTC': str(rustc),
            'RUSTC_WRAPPER': str(wrapper),
            'CARGO_HOME': str((base / 'cargo-home').resolve()),
        }
        cache.packages = {'dep'}
        cache.crates = {'dep'}
        cache.main_names = {'pump'}
        cache.sources = {}
        cache.tools = {}
        cache.configs = {}
        cache.context = {'manifests': {}}
        cache.key = 'test-key'
        cache.entry = cache.root / cache.key
        cache.record = {'key': cache.key, 'status': 'miss', 'seeded_files': 0}
        return cache

    def test_allowed_rejects_nested_deps_subdirectories_and_trailing_newlines(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = self._make_cache(Path(directory))
            self.assertTrue(cache.allowed('sbf-solana-solana/release/deps/libdep-0123456789abcdef.rlib'))
            self.assertTrue(cache.allowed('release/deps/libdep-0123456789abcdef.rlib'))
            self.assertFalse(cache.allowed('release/deps/nested/libdep-0123456789abcdef.rlib'))
            self.assertFalse(cache.allowed('sbf-solana-solana/release/deps/nested/sub/libdep-0123456789abcdef.rlib'))
            self.assertFalse(cache.allowed('release/deps/libdep-0123456789abcdef.rlib\n'))
            self.assertFalse(cache.allowed('C:release/deps/libdep-0123456789abcdef.rlib'))

    def _run_compile_main(self, cache, target, plan):
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if '--build-plan' in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(plan), stderr='')
            for out_path in plan['invocations'][0].get('outputs', []):
                p = Path(out_path)
                if p.parent.exists():
                    p.write_bytes(b'compiled-so')
            return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='')

        log = io.StringIO()
        with patch.object(cache_mod.subprocess, 'run', side_effect=fake_run):
            result = cache.compile_main(target, log)
        return result, calls

    def test_compile_main_accepts_valid_confined_invocation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            cache = self._make_cache(base)
            target = base / 'out/target'
            deps_dir = target / 'sbf-solana-solana/release/deps'
            deps_dir.mkdir(parents=True)
            dep_rlib = deps_dir / 'libdep-0123456789abcdef.rlib'
            dep_rlib.write_bytes(b'rlib')
            out_so = deps_dir / 'pump.so'
            linked_so = target / 'sbf-solana-solana/release/pump.so'
            plan = {
                'invocations': [{
                    'package_name': 'pump',
                    'compile_mode': 'build',
                    'target_kind': ['cdylib'],
                    'program': cache.env['RUSTC_WRAPPER'],
                    'cwd': str(cache.crate),
                    'env': {},
                    'args': [
                        'src/lib.rs',
                        '--out-dir', str(deps_dir),
                        '-L', f'dependency={deps_dir}',
                        '--extern', f'dep={dep_rlib}',
                    ],
                    'outputs': [str(out_so)],
                    'links': {str(linked_so): str(out_so)},
                }],
            }
            result, calls = self._run_compile_main(cache, target, plan)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(len(calls), 2)
            self.assertTrue(cache.record.get('main_freshly_compiled'))
            self.assertEqual(linked_so.read_bytes(), b'compiled-so')

    def test_compile_main_rejects_outside_and_attached_search_paths_and_externs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            cache = self._make_cache(base)
            target = base / 'out/target'
            deps_dir = target / 'release/deps'
            deps_dir.mkdir(parents=True)
            dep_rlib = deps_dir / 'libdep-0123456789abcdef.rlib'
            dep_rlib.write_bytes(b'rlib')

            sibling_target = base / 'out/target-evil/release/deps'
            sibling_target.mkdir(parents=True)
            outside_rlib = base / 'out/outside.rlib'
            outside_rlib.write_bytes(b'evil-rlib')

            bad_arg_lists = [
                ('sibling prefix -L', ['-L', f'dependency={sibling_target}']),
                ('dotdot -L', ['-L', f'dependency={target}/../../outside']),
                ('attached -L/outside', [f'-L{base}']),
                ('attached -Ldependency=/outside', [f'-Ldependency={sibling_target}']),
                ('dangling trailing -L', ['-L']),
                ('dotdot --extern', ['--extern', f'dep={target}/../outside.rlib']),
                ('attached --extern=/outside', [f'--extern=dep={outside_rlib}']),
                ('outside --out-dir', ['--out-dir', str(sibling_target)]),
                ('attached --out-dir=/outside', [f'--out-dir={sibling_target}']),
                ('outside -o', ['-o', str(base / 'out/evil.so')]),
                ('attached -o/outside', [f'-o{base / "out/evil.so"}']),
            ]
            try:
                symlink_rlib = deps_dir / 'libsymlink-0123456789abcdef.rlib'
                symlink_rlib.symlink_to(outside_rlib)
                bad_arg_lists.append(('symlinked --extern inside target', ['--extern', f'dep={symlink_rlib}']))
            except OSError as error:
                if getattr(error, 'winerror', None) != 1314:
                    raise

            for idx, (label, extra_args) in enumerate(bad_arg_lists):
                with self.subTest(label):
                    cache_case = self._make_cache(base)
                    plan = {
                        'invocations': [{
                            'package_name': 'pump',
                            'compile_mode': 'build',
                            'target_kind': ['cdylib'],
                            'program': cache_case.env['RUSTC_WRAPPER'],
                            'cwd': str(cache_case.crate),
                            'env': {},
                            'args': ['src/lib.rs', *extra_args],
                            'outputs': [str(deps_dir / f'pump-{idx}.so')],
                            'links': {},
                        }],
                    }
                    calls = []

                    def fake_run(cmd, **kwargs):
                        calls.append(cmd)
                        if '--build-plan' in cmd:
                            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(plan), stderr='')
                        raise AssertionError(f'main compiler should not be invoked for {label}')

                    with patch.object(cache_mod.subprocess, 'run', side_effect=fake_run):
                        with self.assertRaises((AssertionError, ValueError)):
                            cache_case.compile_main(target, io.StringIO())
                    self.assertEqual(len(calls), 1)

    def test_compile_main_rejects_dotdot_outputs_and_outside_links(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            target = base / 'out/target'
            deps_dir = target / 'release/deps'
            deps_dir.mkdir(parents=True)

            with self.subTest('dotdot output escape'):
                cache_case = self._make_cache(base)
                escaped_out = f'{target}/../escaped.so'
                plan = {
                    'invocations': [{
                        'package_name': 'pump',
                        'compile_mode': 'build',
                        'target_kind': ['cdylib'],
                        'program': cache_case.env['RUSTC_WRAPPER'],
                        'cwd': str(cache_case.crate),
                        'env': {},
                        'args': ['src/lib.rs'],
                        'outputs': [escaped_out],
                        'links': {},
                    }],
                }
                with self.assertRaises((AssertionError, ValueError)):
                    self._run_compile_main(cache_case, target, plan)
                self.assertFalse((base / 'out/escaped.so').exists())

            with self.subTest('outside link destination'):
                cache_case = self._make_cache(base)
                valid_out = deps_dir / 'pump-link.so'
                outside_dest = base / 'clobbered-outside.so'
                plan = {
                    'invocations': [{
                        'package_name': 'pump',
                        'compile_mode': 'build',
                        'target_kind': ['cdylib'],
                        'program': cache_case.env['RUSTC_WRAPPER'],
                        'cwd': str(cache_case.crate),
                        'env': {},
                        'args': ['src/lib.rs'],
                        'outputs': [str(valid_out)],
                        'links': {str(outside_dest): str(valid_out)},
                    }],
                }
                with self.assertRaises((AssertionError, ValueError)):
                    self._run_compile_main(cache_case, target, plan)
                self.assertFalse(outside_dest.exists())
                self.assertNotIn('main_freshly_compiled', cache_case.record)


if __name__ == '__main__':
    unittest.main()
