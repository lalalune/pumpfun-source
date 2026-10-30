"""Real VM regressions for one coherent virtual-reserve input snapshot."""
import base64
from contextlib import ExitStack, redirect_stdout
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('virtual_reserve_driver', ROOT / 'scripts/pump_virtual_reserve_differential.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class VirtualReservePinnedImageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='virtual-reserve-pinning-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        names = [
            'scripts/pump_virtual_reserve_differential.py',
            'scripts/pump_set_mayhem_virtual_params_differential.py',
            'scripts/pump_amm_reusable_harness.py', 'scripts/fixtures/signer_stub.so',
            'evidence/original/pump/deployed.so',
            'evidence/dependencies/spl_token_2022/deployed.so',
            'evidence/dependencies/associated_token/deployed.so',
            'research/imported-lab/analysis/pump_fun/config-snapshot.json',
        ]
        for name in names:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.candidate = self.root / 'candidate.so'
        shutil.copyfile(self.root / 'evidence/original/pump/deployed.so', self.candidate)
        self.output = self.root / 'receipt.json.gz'
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(driver, '__file__', str(self.root / names[0])))
        stack.enter_context(patch.object(driver.f, '__file__', str(self.root / names[1])))
        stack.enter_context(patch.object(driver.f, 'ROOT', self.root))
        stack.enter_context(patch.object(driver.f, 'ORIGINAL', self.root / 'evidence/original/pump/deployed.so'))
        stack.enter_context(patch.object(driver.f, 'STUB', self.root / 'scripts/fixtures/signer_stub.so'))
        # A successful state-mutating case and a genuine authority-error case.
        base = dict(rqr=5_000_000_000, vtr=10**15, rtr=800_000_000_000_000,
                    tts=10**15, vqr=30_000_000_000, vault=0, irtr=793_100_000_000_000,
                    spl=False, mayhem=True)
        self.bounded_cases = [dict(base, name='success'), dict(base, name='missing-authority', direct=True)]

    def invoke(self, *, mutate=None, all_cases=False, build=None):
        arguments = ['virtual-reserve', '--candidate', str(self.candidate), '--output', str(self.output)]
        if build is not None:
            arguments += ['--build-comparison', str(build)]
        real_run = driver.run
        calls = 0

        def run(*args, **kwargs):
            nonlocal calls
            result = real_run(*args, **kwargs)
            calls += 1
            if calls == 1 and mutate is not None:
                mutate()
            return result

        with ExitStack() as stack:
            stack.enter_context(patch.object(sys, 'argv', arguments))
            stack.enter_context(patch.object(driver, 'run', run))
            if not all_cases:
                stack.enter_context(patch.object(driver, 'cases', lambda: iter(self.bounded_cases)))
            stack.enter_context(redirect_stdout(io.StringIO()))
            driver.main()
        return json.loads(gzip.decompress(self.output.read_bytes()))

    def assert_matches(self, report, count):
        self.assertEqual(report['case_count'], count)
        self.assertEqual(len(report['cases']), count)
        self.assertEqual(report['mismatches'], [])
        self.assertTrue(any(row['original']['error'] is None for row in report['cases']))
        self.assertTrue(any(row['original']['error'] is not None for row in report['cases']))
        self.assertTrue(any(row['original']['events'] for row in report['cases']))
        for row in report['cases']:
            self.assertEqual(row['differences'], [])
            self.assertEqual(row['original']['transaction_base64'], row['candidate']['transaction_base64'])

    def build_binding(self):
        source = self.root / 'programs/pump/src/lib.rs'
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('// declared source fixture; no build is claimed\n')
        manifest = driver.source_manifest(self.root / 'programs/pump', self.root / 'programs/pump', self.root)
        build = self.root / 'build.json'
        build.write_text(json.dumps({'comparison': {'candidate_sha256': hashlib.sha256(self.candidate.read_bytes()).hexdigest()},
                                     'source_sha256': manifest}))
        return build, source, manifest

    def test_full_real_corpus_matches_and_receipt_binds_loaded_images(self):
        report = self.invoke(all_cases=True)
        self.assert_matches(report, 192)
        self.assertEqual(report['candidate_sha256'], driver.RETAINED_SHA256['original'])
        self.assertEqual(report['original_sha256'], driver.RETAINED_SHA256['original'])
        for name, path in driver.program_paths().items():
            self.assertEqual(report['inputs_sha256'][str(path.relative_to(self.root))], driver.RETAINED_SHA256[name])

    def test_live_candidate_replacement_after_first_execution_does_not_change_run(self):
        replacement = (ROOT / 'evidence/original/pump_fees/deployed.so').read_bytes()
        build, _, manifest = self.build_binding()
        report = self.invoke(mutate=lambda: self.candidate.write_bytes(replacement), build=build)
        self.assert_matches(report, 2)
        self.assertEqual(report['compiled_source_sha256'], manifest)
        self.assertEqual(report['candidate_sha256'], driver.RETAINED_SHA256['original'])
        self.assertNotEqual(hashlib.sha256(self.candidate.read_bytes()).hexdigest(), report['candidate_sha256'])

    def test_all_original_and_dependency_images_are_frozen_before_execution(self):
        for name in driver.RETAINED_SHA256:
            with self.subTest(image=name):
                # Each invocation has a distinct source path, avoiding process-wide cache reuse.
                with tempfile.TemporaryDirectory(dir=self.root) as directory:
                    prior = driver.program_paths()[name]
                    source = Path(directory) / 'image.so'
                    source.write_bytes(prior.read_bytes())
                    self.output = Path(directory) / 'receipt.json.gz'
                    paths = driver.program_paths()
                    paths[name] = source
                    with patch.object(driver, 'program_paths', return_value=paths):
                        report = self.invoke(mutate=lambda: source.write_bytes(b'changed after pin'))
                    self.assert_matches(report, 2)
                    self.assertEqual(report['inputs_sha256'][str(source.relative_to(self.root))], driver.RETAINED_SHA256[name])

    def test_configuration_used_and_hashed_is_the_same_snapshot(self):
        path = self.root / 'research/imported-lab/analysis/pump_fun/config-snapshot.json'
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        with patch.object(driver.f, 'CAPTURE', {'data_base64': base64.b64encode(b'wrong import-time data').decode()}):
            report = self.invoke(mutate=lambda: path.write_bytes(b'changed after load'))
        self.assert_matches(report, 2)
        self.assertEqual(report['inputs_sha256'][str(path.relative_to(self.root))], expected)

    def test_wrong_retained_image_is_rejected_before_execution(self):
        for name in driver.RETAINED_SHA256:
            with self.subTest(image=name), tempfile.TemporaryDirectory(dir=self.root) as directory:
                paths = driver.program_paths()
                wrong = Path(directory) / 'wrong.so'
                shutil.copyfile(ROOT / 'evidence/original/pump_fees/deployed.so', wrong)
                paths[name] = wrong
                with patch.object(driver, 'program_paths', return_value=paths):
                    with self.assertRaisesRegex(ValueError, 'image hash mismatch'):
                        self.invoke()
                self.assertFalse(self.output.exists())

    def test_wrong_candidate_is_a_real_vm_mismatch_not_a_passing_receipt(self):
        shutil.copyfile(ROOT / 'evidence/original/pump_fees/deployed.so', self.candidate)
        with self.assertRaises(SystemExit) as raised:
            self.invoke()
        self.assertEqual(raised.exception.code, 1)
        report = json.loads(gzip.decompress(self.output.read_bytes()))
        self.assertTrue(report['mismatches'])
        self.assertEqual(report['candidate_sha256'], hashlib.sha256(self.candidate.read_bytes()).hexdigest())

    def test_declared_source_change_during_execution_is_rejected(self):
        build, source, _ = self.build_binding()
        with self.assertRaisesRegex(ValueError, 'source changed during run'):
            self.invoke(mutate=lambda: source.write_text('// changed source\n'), build=build)
        self.assertFalse(self.output.exists())

    def test_wrong_build_binding_is_rejected(self):
        build = self.root / 'build.json'
        environment = dict(os.environ, PYTHONPATH=str(ROOT / 'scripts'))
        environment.pop('PYTHONOPTIMIZE', None)
        for document, message in [(None, 'invalid build comparison'), ({}, 'invalid build comparison'),
                                  ({'comparison': {'candidate_sha256': '0' * 64}, 'source_sha256': '0' * 64},
                                   'candidate does not match build comparison')]:
            with self.subTest(document=document):
                build.write_text(json.dumps(document))
                result = self.run_differential([], build, environment)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.output.exists())

    def test_optimized_python_is_refused_before_the_binding_checks(self):
        # The script now requires normal Python, so -O stops at its guard instead
        # of reaching the build-binding raises below it. Assert the guard rather
        # than a binding message that optimized runs can no longer produce.
        build = self.root / 'build.json'
        build.write_text(json.dumps({'comparison': {'candidate_sha256': '0' * 64},
                                     'source_sha256': '0' * 64}))
        environment = dict(os.environ, PYTHONPATH=str(ROOT / 'scripts'))
        environment.pop('PYTHONOPTIMIZE', None)
        optimized = dict(environment, PYTHONOPTIMIZE='1')
        for flags, env in ((['-O'], environment), (['-OO'], environment), ([], optimized)):
            with self.subTest(flags=flags, optimize=env.get('PYTHONOPTIMIZE')):
                result = self.run_differential(flags, build, env)
                self.assertEqual(result.returncode, 1)
                self.assertIn('Normal Python is required', result.stderr)
                self.assertFalse(self.output.exists())

    def run_differential(self, python_flags, build, environment):
        return subprocess.run([sys.executable, *python_flags,
                               str(self.root / 'scripts/pump_virtual_reserve_differential.py'),
                               '--candidate', str(self.candidate), '--build-comparison', str(build),
                               '--output', str(self.output)], env=environment, capture_output=True, text=True, timeout=30)


if __name__ == '__main__':
    unittest.main()
