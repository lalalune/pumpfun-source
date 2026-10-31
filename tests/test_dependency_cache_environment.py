"""Real rustc env-dep parsing and optional full verified SBF cache reuse proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from pump_dependency_cache import dep_info_environment

RUSTC = (str(Path(os.environ['PUMP_TEST_RUST_BIN'])/'rustc')
         if os.environ.get('PUMP_TEST_RUST_BIN') else shutil.which('rustc'))


class CompilerEnvironmentTests(unittest.TestCase):
    @unittest.skipUnless(RUSTC, 'rustc is required for actual dependency-info emission')
    def test_actual_rustc_bindings_preserve_escapes_unicode_and_unset_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, info = root/'probe.rs', root/'probe.d'
            source.write_text('pub const VALUE:&str=env!("PROBE_VALUE");\n'
                              'pub const OPTIONAL:Option<&str>=option_env!("PROBE_OPTION");\n')
            value = 'line\nreturn\rslash\\equal=ß\x85continued'
            env = dict(os.environ, PROBE_VALUE=value)
            env.pop('PROBE_OPTION', None)
            for optional in (None, ''):
                with self.subTest(optional=optional):
                    if optional is not None:
                        env['PROBE_OPTION'] = optional
                    result = subprocess.run([RUSTC, '--crate-name', 'probe', '--crate-type', 'lib',
                                             '--emit=dep-info='+str(info), str(source)],
                                            env=env, capture_output=True, text=True, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(dep_info_environment(info.read_text()),
                                     {'PROBE_VALUE': value, 'PROBE_OPTION': optional})

    def test_unrecognized_escape_cannot_certify_a_cached_binding(self):
        for text in ('# env-dep:VALUE=invalid\\x', '# env-dep:VALUE=trailing\\',
                     '# env-dep:VALUE=A\n# env-dep:VALUE=B'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                dep_info_environment(text)

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_BUILD_TEST_SDK'),
                         'set PUMP_BUILD_TEST_SDK to an authenticated v1.44 macOS SDK')
    def test_real_verified_sbf_cache_rebuilds_only_when_declared_bindings_change(self):
        probe = ROOT/'research/dependency-cache-env-20261101/probe.py'
        run = subprocess.run([sys.executable, '-B', str(probe), str(ROOT), os.environ['PUMP_BUILD_TEST_SDK']],
                             capture_output=True, text=True, timeout=300)
        self.assertEqual(run.returncode, 0, run.stderr)
        rows = json.loads(run.stdout)
        initial = rows['initial']['candidate_sha256']
        for name in ('same', 'unrelated'):
            self.assertEqual(rows[name]['returncode'], 0, rows[name])
            self.assertEqual(rows[name]['cache_status'], 'hit')
            self.assertEqual(rows[name]['candidate_sha256'], initial)
        for changed, fresh in [('changed', 'fresh_b'), ('optional', 'fresh_optional'),
                               ('escaped', 'fresh_escaped')]:
            self.assertEqual(rows[changed]['returncode'], 0, rows[changed])
            self.assertEqual(rows[changed]['cache_status'], 'bypass')
            self.assertNotEqual(rows[changed]['candidate_sha256'], initial)
            self.assertEqual(rows[changed]['candidate_sha256'], rows[fresh]['candidate_sha256'])
            self.assertTrue(rows[changed]['source_unchanged'])
        self.assertEqual(rows['changed']['changed_environment_dependencies'], ['PROBE_DEPENDENCY_VALUE'])
        self.assertEqual(rows['optional']['changed_environment_dependencies'], ['PROBE_OPTION'])
        self.assertEqual(rows['escaped_repeat']['cache_status'], 'hit')
        self.assertEqual(rows['escaped_repeat']['candidate_sha256'], rows['fresh_escaped']['candidate_sha256'])
        self.assertNotEqual(rows['missing']['returncode'], 0)
        self.assertNotIn('candidate_sha256', rows['missing'])
        self.assertIn('environment variable `PROBE_DEPENDENCY_VALUE` not defined', rows['missing']['log'])


if __name__ == '__main__':
    unittest.main()
