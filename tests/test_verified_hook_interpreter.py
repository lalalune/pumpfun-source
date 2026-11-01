"""Selected-interpreter launchers and their cache identity; optional real SDK proof."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from pump_dependency_cache import DependencyCache, sha

HOOKS = ('pump_physical_source_wrapper', 'pump_text_layout_rustc', 'pump_text_layout_linker')
METADATA = json.dumps({'resolve': {'root': 'main'}, 'packages': [
    {'id': 'main', 'name': 'pump', 'targets': [{'name': 'pump', 'kind': ['cdylib']}]}]})


class VerifiedHookTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'shell hooks require POSIX')
    def test_each_launcher_preserves_selected_interpreter_and_arguments(self):
        with tempfile.TemporaryDirectory(prefix='verified hook ') as temporary:
            root = Path(temporary).resolve()
            environment = root/'selected Python'
            venv.EnvBuilder(with_pip=False).create(environment)
            selected = environment/'bin/python'
            empty = root/'empty'
            empty.mkdir()
            arguments = ['a b', '', 'quote\'"\\', '$LITERAL;still-one-argument']
            for name in HOOKS:
                with self.subTest(hook=name):
                    launcher = root/(name+'.sh')
                    shutil.copy2(ROOT/'scripts'/(name+'.sh'), launcher)
                    # This unit fixture isolates the real launcher's routing.
                    # The SDK proof below executes the unchanged hook bodies.
                    (root/(name+'.py')).write_text(
                        'import json,sys;print(json.dumps([sys.executable,sys.argv[1:]]))\n', encoding='utf-8')
                    env = dict(os.environ, PATH=str(empty), PUMP_VERIFIED_PYTHON=str(selected))
                    run = subprocess.run([str(launcher), *arguments], env=env, capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertEqual(json.loads(run.stdout), [str(selected), arguments])
                    del env['PUMP_VERIFIED_PYTHON']
                    refused = subprocess.run([str(launcher)], env=env, capture_output=True)
                    self.assertNotEqual(refused.returncode, 0)
                    self.assertIn(b'must select Python', refused.stderr)

    def cache(self, root, launcher=None, python=sys.executable):
        crate, sdk, cargo = [root/name for name in ('crate', 'sdk', 'cargo')]
        for path in (crate, sdk, cargo):
            path.mkdir(exist_ok=True)
        (crate/'Cargo.toml').write_text('[package]\nname="pump"\nversion="0.1.0"\n')
        wrapper = root/'wrapper.py'
        wrapper.write_text('wrapper implementation\n')
        env = {'CARGO_HOME': str(cargo), 'PUMP_VERIFIED_PYTHON': python}
        with mock.patch('pump_dependency_cache.subprocess.check_output', return_value=METADATA):
            return DependencyCache(root/'cache', root, crate, crate, sdk, env, wrapper,
                                   direct=True, wrapper_launcher=launcher)

    def test_launcher_and_selected_python_are_cache_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = root/'wrapper.sh'
            launcher.write_text('launcher one\n')
            legacy = self.cache(root)
            first = self.cache(root, launcher)
            repeat = self.cache(root, launcher)
            self.assertNotIn('wrapper_launcher_sha256', legacy.context)
            self.assertNotEqual(legacy.key, first.key)
            self.assertEqual(first.key, repeat.key)
            self.assertEqual(first.context['wrapper_launcher_sha256'], sha(launcher))
            launcher.write_text('launcher two\n')
            changed = self.cache(root, launcher)
            self.assertNotEqual(first.key, changed.key)
            self.assertNotEqual(changed.key, self.cache(root, launcher, str(root/'another-python')).key)

    def test_seed_must_name_the_same_launcher_and_interpreter(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            launcher = root/'wrapper.sh'
            launcher.write_text('launcher\n')
            cache = self.cache(root, launcher)
            cache.tools = {'rust/bin/rustc': 'rustc', 'rust/bin/cargo': 'cargo'}
            seed = root/'seed'
            seed.mkdir()
            for name in ('candidate.so', 'unstripped.so'):
                (seed/name).write_bytes(b'explicit synthetic seed fixture')
            base = {'returncode': 0, 'source_unchanged': True,
                    'source_sha256': {'wrapper.py': sha(root/'wrapper.py')},
                    'comparison': {'candidate_sha256': sha(seed/'candidate.so')},
                    'unstripped_sha256': sha(seed/'unstripped.so'),
                    'tool_sha256': {'rustc': 'rustc', 'cargo': 'cargo'},
                    'source_wrapper_sha256': cache.context['wrapper_sha256'],
                    'source_wrapper_launcher_sha256': sha(launcher),
                    'environment': {'PUMP_VERIFIED_PYTHON': sys.executable}}
            for mismatch in ('missing-launcher', 'launcher', 'python'):
                report = json.loads(json.dumps(base))
                if mismatch == 'missing-launcher':
                    del report['source_wrapper_launcher_sha256']
                elif mismatch == 'launcher':
                    report['source_wrapper_launcher_sha256'] = '0'*64
                else:
                    report['environment']['PUMP_VERIFIED_PYTHON'] = 'different-python'
                (seed/'build-comparison.json').write_text(json.dumps(report), encoding='utf-8')
                message = 'seed compiler wrapper Python differs' if mismatch == 'python' else 'seed compiler wrapper launcher differs'
                with self.subTest(mismatch=mismatch), self.assertRaisesRegex(AssertionError, message):
                    cache.import_clean_build(seed)
                self.assertFalse(cache.entry.exists())

    @unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK'), 'requires official v1.44 SDK')
    def test_real_verified_builder_without_python_on_path(self):
        path = ROOT/'research/verified-hook-interpreter-20261101/probe.py'
        spec = importlib.util.spec_from_file_location('verified_hook_probe', path)
        probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(probe)
        with tempfile.TemporaryDirectory() as temporary:
            result = probe.run(ROOT, Path(os.environ['PUMP_BUILD_TEST_SDK']), Path(temporary)/'proof')
        probe.validate(result, 'fixed')
        self.assertEqual(len(result['cases']), 11)


if __name__ == '__main__':
    unittest.main()
