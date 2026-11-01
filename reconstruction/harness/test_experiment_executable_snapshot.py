"""Do not re-resolve a tool alias after its old target has been fingerprinted."""
import os
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import experiment_runner as runner


class ExecutableSnapshotTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='experiment-tool-snapshot-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'input').write_text('unchanged source\n')

    def swap(self, alias, target):
        replacement = alias.with_name(alias.name + '.next')
        replacement.symlink_to(target)
        replacement.replace(alias)

    def run_during_tool_switch(self, alias, new_target, args):
        real_identity = runner.identity

        def switch_after_admission(*values, **kwargs):
            admitted = real_identity(*values, **kwargs)
            self.swap(alias, new_target)
            return admitted

        with patch.object(runner, 'identity', switch_after_admission):
            return runner.run_trial(self.source, [str(alias), *args], self.root / 'trial')

    @unittest.skipUnless(shutil.which('false'), 'requires a native false executable')
    def test_tool_switch_cannot_cache_a_pass_for_the_old_failing_command(self):
        old = Path(shutil.which('false'))
        alias = self.root / 'false'
        alias.symlink_to(old)
        args = ['-c', 'print("a different real executable ran")']
        self.assertEqual(subprocess.run([str(alias), *args], capture_output=True).returncode, 1)
        first = self.run_during_tool_switch(alias, Path(sys.executable).resolve(), args)
        self.swap(alias, old)
        cached = runner.run_trial(self.source, [str(alias), *args], self.root / 'trial')
        self.assertEqual(first['status'], 'fail', 'a different executable produced a cached pass')
        self.assertTrue(cached['reused'])
        self.assertEqual(cached['status'], 'fail')
        self.assertIn(str(old.resolve()), first['inputs']['inputs'])
        self.assertEqual(first['inputs']['executable'], str(old.resolve()))

    def test_environment_change_cannot_produce_a_cached_result_for_old_environment(self):
        variable = 'PUMP_EXPERIMENT_TEST_VALUE'
        command = [sys.executable, '-c',
                   f'import os; raise SystemExit(0 if os.environ.get({variable!r}) == "old" else 1)']
        real_identity = runner.identity

        def change_after_admission(*values, **kwargs):
            admitted = real_identity(*values, **kwargs)
            os.environ[variable] = 'new'
            return admitted

        with patch.dict(os.environ, {variable: 'old'}):
            with patch.object(runner, 'identity', change_after_admission):
                first = runner.run_trial(self.source, command, self.root / 'trial')
            os.environ[variable] = 'old'
            cached = runner.run_trial(self.source, command, self.root / 'trial')
        self.assertEqual(first['status'], 'pass', 'child used a different environment than its receipt')
        self.assertTrue(cached['reused'])
        self.assertEqual(cached['status'], 'pass')

    def test_caller_command_mutation_cannot_change_admitted_arguments(self):
        admitted_code = 'print("admitted arguments"); raise SystemExit(0)'
        command = [sys.executable, '-c', admitted_code]
        real_copy = runner.shutil.copytree

        def mutate_after_staging(*values, **kwargs):
            copied = real_copy(*values, **kwargs)
            command[-1] = 'print("different arguments"); raise SystemExit(1)'
            return copied

        with patch.object(runner.shutil, 'copytree', mutate_after_staging):
            first = runner.run_trial(self.source, command, self.root / 'trial')
        command[-1] = admitted_code
        cached = runner.run_trial(self.source, command, self.root / 'trial')
        self.assertEqual(first['key'], runner.digest(json.dumps(first['inputs'], sort_keys=True).encode()),
                         'stored admission changed after its cache key was computed')
        self.assertEqual(first['status'], 'pass')
        self.assertTrue(cached['reused'])
        log = self.root / 'trial' / first['attempt'] / 'stdout.log'
        self.assertEqual(log.read_bytes(), b'admitted arguments\n')

    def test_declared_script_alias_change_cannot_cache_a_different_program(self):
        old = self.root / 'old.py'
        old.write_text('raise SystemExit(1)\n')
        new = self.root / 'new.py'
        new.write_text('raise SystemExit(0)\n')
        alias = self.root / 'script.py'
        alias.symlink_to(old)
        real_identity = runner.identity

        def switch_after_admission(*values, **kwargs):
            admitted = real_identity(*values, **kwargs)
            self.swap(alias, new)
            return admitted

        with patch.object(runner, 'identity', switch_after_admission):
            result = runner.run_trial(self.source, [sys.executable, str(alias)],
                                      self.root / 'trial', inputs=[alias])
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['returncode'], 'retargeted script was launched')
        self.assertEqual(result['inputs']['declared_input_paths'][str(alias)], str(old.resolve()))
        self.swap(alias, old)
        retried = runner.run_trial(self.source, [sys.executable, str(alias)],
                                   self.root / 'trial', inputs=[alias])
        self.assertEqual(retried['status'], 'fail')
        self.assertFalse(retried['reused'])

    def test_retargeted_input_during_execution_cannot_produce_a_pass(self):
        old, new, alias = (self.root / name for name in ('old.py', 'new.py', 'script.py'))
        code = (f'from pathlib import Path\np = Path({str(alias)!r})\n'
                f'p.unlink()\np.symlink_to({str(new)!r})\n')
        old.write_text(code)
        new.write_text(code)  # Equal contents do not make the resolved path stable.
        alias.symlink_to(old)
        result = runner.run_trial(self.source, [sys.executable, str(alias)],
                                  self.root / 'trial', inputs=[alias])
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['status'], 'error')
        self.assertIn('declared input changed', result['reason'])

    @unittest.skipUnless(shutil.which('false'), 'requires a native false executable')
    def test_changed_executable_bytes_are_rejected_before_launch(self):
        executable = self.root / 'false'
        shutil.copyfile(shutil.which('false'), executable)
        executable.chmod(0o755)
        real_identity = runner.identity

        def change_after_admission(*values, **kwargs):
            admitted = real_identity(*values, **kwargs)
            executable.write_bytes(b'changed binary')
            return admitted

        with patch.object(runner, 'identity', change_after_admission):
            result = runner.run_trial(self.source, [str(executable)], self.root / 'trial')
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['returncode'])
        log = self.root / 'trial' / result['attempt'] / 'stderr.log'
        self.assertIn(b'declared input changed before launch', log.read_bytes())

    def test_loaded_driver_hash_cannot_be_relabelled_by_disk_edit(self):
        driver = self.root / 'driver.py'
        loaded_bytes = Path(runner.__file__).read_bytes()
        supervisor = self.root / 'process_supervisor.py'
        supervisor_bytes = runner.SUPERVISOR_PATH.read_bytes()
        driver.write_bytes(loaded_bytes)
        supervisor.write_bytes(supervisor_bytes)
        spec = importlib.util.spec_from_file_location('snapshot_driver', driver)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        driver.write_bytes(loaded_bytes + b'\n# later disk revision\n')
        supervisor.write_bytes(supervisor_bytes + b'\n# later supervisor revision\n')
        result = loaded.run_trial(self.source, [sys.executable, '-c', 'pass'],
                                  self.root / 'trial')
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['inputs']['runner_sha256'], runner.digest(loaded_bytes))
        self.assertNotEqual(result['inputs']['runner_sha256'], runner.digest(driver.read_bytes()))
        self.assertEqual(result['inputs']['supervisor_sha256'], runner.digest(supervisor_bytes))
        self.assertNotEqual(result['inputs']['supervisor_sha256'],
                            runner.digest(supervisor.read_bytes()))

    def test_supervisor_source_admission_ignores_valid_executable_bytecode_cache(self):
        import importlib._bootstrap_external as bytecode
        driver = self.root / 'experiment_runner.py'
        supervisor = self.root / 'process_supervisor.py'
        marker = self.root / 'cache-executed'
        raw = runner.SUPERVISOR_PATH.read_bytes()
        supervisor.write_bytes(raw)
        driver.write_bytes(Path(runner.__file__).read_bytes())
        injected = ('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n').encode() + raw
        code = compile(injected, str(supervisor), 'exec')
        metadata = supervisor.stat()
        cache = Path(importlib.util.cache_from_source(str(supervisor)))
        cache.parent.mkdir()
        cache.write_bytes(bytecode._code_to_timestamp_pyc(code, int(metadata.st_mtime), metadata.st_size))
        # Prove this is executable cached code for the clean source file.
        spec = importlib.util.spec_from_file_location('private_cached_supervisor', supervisor)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        self.assertTrue(marker.exists())
        marker.unlink()
        result = subprocess.run([sys.executable, '-I', '-B', '-c',
            'import sys;sys.path.insert(0,sys.argv[1]);import experiment_runner as E;print(E.IMPLEMENTATION_SHA256)',
            str(self.root)], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(result.stdout.strip(), runner.digest(raw))

    @unittest.skipUnless(os.environ.get('PUMP_BUILD_TEST_SDK') and shutil.which('rustc'),
                         'requires the explicit SBF SDK and a host rustc')
    def test_real_rustc_probe_executes_the_compiler_it_hashed(self):
        sdk = Path(os.environ['PUMP_BUILD_TEST_SDK']).resolve() / 'rust/bin/rustc'
        host = Path(shutil.which('rustc'))
        old = subprocess.check_output([str(sdk), '--version'], cwd=self.root)
        new = subprocess.check_output([str(host), '--version'], cwd=self.root)
        if old == new:
            self.skipTest('host and SDK rustc versions are identical')
        alias = self.root / 'rustc'
        alias.symlink_to(sdk)
        first = self.run_during_tool_switch(alias, host, ['--version'])
        self.swap(alias, sdk)
        cached = runner.run_trial(self.source, [str(alias), '--version'], self.root / 'trial')
        log = self.root / 'trial' / first['attempt'] / 'stdout.log'
        self.assertEqual(log.read_bytes(), old, 'receipt hashed SDK rustc but executed host rustc')
        self.assertTrue(cached['reused'])
        self.assertEqual(first['inputs']['executable'], str(sdk.resolve()))


if __name__ == '__main__':
    unittest.main()
