"""Keep compiler results when a UTF-8 log is read under an ASCII locale.

The always-on CLI tests reuse the existing stub SDK and real file publication;
the optional SDK test runs thirteen genuine offline builds separately.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_pump_build_verified_tool_binding import BUILDER, ROOT, make_sdk


def load_probe():
    path = ROOT/'research/verified-compiler-log-utf8-20261101/probe.py'
    spec = importlib.util.spec_from_file_location('verified_log_probe', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerifiedLogEncodingTests(unittest.TestCase):
    def cli(self, payload, code, mode):
        with tempfile.TemporaryDirectory(prefix='verified-log-encoding-') as temporary:
            root = Path(temporary)
            sdk = make_sdk(root, swap=False)
            cargo = sdk/'rust/bin/cargo'
            original = cargo.read_text(encoding='utf-8')
            # Explicit synthetic transport; actual compiler proof is below.
            cargo.write_text('#!/usr/bin/env python3\nimport os\nos.write(2, '+repr(payload)+')\n'
                             + ('raise SystemExit('+str(code)+')\n' if code else original), encoding='utf-8')
            output = root/'out'
            run = subprocess.run([sys.executable, '-B', '-X', 'utf8='+str(mode), str(BUILDER),
                '--sdk', str(sdk), '--registry-home', str(root/'registry'), '--output', str(output)],
                env=dict(os.environ, LC_ALL='C', PYTHONUTF8=str(mode), PYTHONCOERCECLOCALE='0'),
                capture_output=True, timeout=30)
            attempt = json.loads((output/'build-attempt.json').read_text(encoding='utf-8'))
            return run, attempt, (output/'build.log').read_bytes(), (output/'build-comparison.json').exists()

    def test_warning_and_failure_keep_the_compiler_status_and_log(self):
        for mode in (1, 0):
            for code in (0, 101):
                with self.subTest(mode=mode, compiler_code=code):
                    run, attempt, log, published = self.cli('diagnostic: caf\u00e9\n'.encode(), code, mode)
                    self.assertNotIn(b'UnicodeDecodeError', run.stderr)
                    self.assertEqual(attempt['returncode'], code)
                    self.assertTrue(attempt['source_unchanged'])
                    self.assertEqual(attempt['build_log_sha256'], load_probe().sha(log))
                    self.assertEqual(run.returncode == 0, code == 0)
                    self.assertEqual(published, code == 0)

    def test_invalid_utf8_is_not_replaced_or_accepted(self):
        for mode in (1, 0):
            with self.subTest(mode=mode):
                run, attempt, log, published = self.cli(b'invalid: \xff\n', 0, mode)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn(b'UnicodeDecodeError', run.stderr)
                self.assertFalse(published)
                self.assertIn(b'\xff', log)

    def test_cache_log_publication_handles_unicode_and_rejects_invalid_utf8(self):
        driver = '''
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1])/'scripts'))
from test_pump_dependency_cache_cargo_log import finish_fixture
with finish_fixture(['warning: caf\\u00e9']) as (cache,target,log,report):
    cache.finish(target,log,report)
    assert json.loads((cache.entry/'MANIFEST.json').read_text(encoding='utf-8'))['files']
with finish_fixture([]) as (cache,target,log,report):
    log.write_bytes(b'invalid: \\xff\\n')
    try: cache.finish(target,log,report)
    except UnicodeDecodeError: pass
    else: raise AssertionError('invalid UTF-8 accepted')
    assert not cache.entry.exists()
'''
        for mode in (1, 0):
            run = subprocess.run([sys.executable, '-B', '-X', 'utf8='+str(mode), '-c', driver, str(ROOT)],
                env=dict(os.environ, LC_ALL='C', PYTHONUTF8=str(mode), PYTHONCOERCECLOCALE='0'),
                capture_output=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stderr.decode('utf-8', errors='replace'))

    @unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires an explicit official v1.44 SDK')
    def test_real_offline_compiler_warning_failure_and_cache_paths(self):
        with tempfile.TemporaryDirectory(prefix='verified-log-sdk-') as temporary:
            result = load_probe().run_probe(ROOT, Path(os.environ['PUMP_BUILD_TEST_SDK']), Path(temporary)/'proof')
        self.assertEqual(len(result['cases']), 13)
        for name, row in result['cases'].items():
            with self.subTest(case=name):
                failed = 'failure' in name
                self.assertFalse(row['decode_error'])
                expected_code = (1 if name.startswith('cache-failure') else 101) if failed else 0
                self.assertEqual(row['compiler_returncode'], expected_code)
                self.assertEqual(row['comparison_published'], not failed)
                self.assertTrue(row['source_unchanged'])
                self.assertTrue(row['dependency_inputs_unchanged'])
                self.assertTrue(row['log_hash_recorded'])
                self.assertTrue(row['log_contains_message'])
        cases = result['cases']
        for kind in ('ascii', 'unicode'):
            self.assertEqual(cases[kind+'-warning-1']['candidate_sha256'], cases[kind+'-warning-0']['candidate_sha256'])
        self.assertEqual(cases['cache-hit-0']['cache_status'], 'hit')
        self.assertEqual(cases['cache-seed-1']['candidate_sha256'], cases['cache-hit-0']['candidate_sha256'])
        self.assertEqual(cases['cache-seed-1']['candidate_sha256'], cases['cache-miss-0']['candidate_sha256'])
        for name in ('copied_capture_unchanged', 'caller_inputs_unchanged', 'tools_unchanged'):
            self.assertTrue(result[name])


if __name__ == '__main__':
    unittest.main()
