"""A failed nested-runtime preparation must not publish a partial packet."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
PREFIX = 'runtime-layer/nested-harness/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class NestedRuntimePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='nested-runtime-publication-')
        self.root = Path(self.temporary.name)
        candidate = self.root / 'repro/pump/pkg/main/candidate.so'
        candidate.parent.mkdir(parents=True)
        candidate.write_bytes(b'candidate')
        sources = {}
        for index in range(37):
            path = self.root / f'programs/pump/src/f{index}.rs'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f'// source {index}\n')
            sources[str(path.relative_to(self.root))] = sha(path.read_bytes())
        self.sources = sources
        main = candidate.parent
        (main / 'build-comparison.json').write_text(json.dumps({
            'source_sha256': sources,
            'comparison': {'candidate_sha256': sha(candidate.read_bytes())},
        }))
        (main / 'build-attempt.json').write_text(json.dumps({
            'returncode': 0,
            'source_unchanged': True,
            'source_sha256': sources,
            'source_after_sha256': sources,
        }))
        status = {
            'pump': {
                'candidate_artifact': str(candidate.relative_to(self.root)),
                'comparison_report': str(
                    (main / 'build-comparison.json').relative_to(self.root)),
            }
        }
        (self.root / 'repro/status.json').write_text(json.dumps(status))

        package = self.root / 'repro/pump/buy-mode-order-fortyeight'
        harness = package / PREFIX
        harness.mkdir(parents=True)
        manifest = {}
        for index in range(5):
            path = harness / f'h{index}.py'
            path.write_text(f'# harness {index}\n')
            manifest[f'{PREFIX}h{index}.py'] = {'sha256': sha(path.read_bytes())}
        source_map = harness / 'expected-source-map.json'
        source_map.write_text('{}\n')
        manifest[f'{PREFIX}expected-source-map.json'] = {
            'sha256': sha(source_map.read_bytes())}
        (package / 'manifest.json').write_text(json.dumps(manifest))

        stub = types.ModuleType('verify_current_checkpoint')
        stub.verify = lambda name, root: {
            'candidate_sha256': sha(candidate.read_bytes())}
        self.checkpoint_stub = stub
        self.load_tool()

    def load_tool(self):
        spec = importlib.util.spec_from_file_location(
            'nested_runtime_under_test',
            SCRIPTS / 'prepare_pump_nested_runtime.py',
        )
        module = importlib.util.module_from_spec(spec)
        with mock.patch.dict(sys.modules, {'verify_current_checkpoint': self.checkpoint_stub}):
            spec.loader.exec_module(module)
        module.ROOT = self.root
        module.HARNESS_PACKAGE = self.root / 'repro/pump/buy-mode-order-fortyeight'
        module.HARNESS_SEAL = sha((module.HARNESS_PACKAGE / 'manifest.json').read_bytes())
        self.tool = module

    def tearDown(self):
        self.temporary.cleanup()

    def test_copy_failure_publishes_nothing_and_preserves_rerun_path(self):
        output = self.root / 'prepared'
        real_write_bytes = Path.write_bytes

        def fail_second_harness_file(path, data):
            if path.name == 'h1.py':
                raise OSError('injected harness copy failure')
            return real_write_bytes(path, data)

        with mock.patch.object(Path, 'write_bytes', fail_second_harness_file):
            with self.assertRaisesRegex(OSError, 'injected harness copy failure'):
                self.tool.prepare(output)

        self.assertFalse(output.exists(), 'failed preparation published a partial runtime')
        self.assertEqual(list(output.parent.glob('.prepared.*')), [])

    def test_successful_preparation_publishes_complete_binding(self):
        output = self.root / 'prepared'
        record = self.tool.prepare(output)
        self.assertEqual(record['status'], 'PASS')
        self.assertEqual(len(record['copied_harness_sha256']), 6)
        self.assertTrue((output / 'binding-update.json').is_file())
        self.assertEqual(list(output.parent.glob('.prepared.*')), [])

    def test_late_empty_destination_is_not_replaced(self):
        output = self.root / 'prepared'
        write_text = Path.write_text
        def concurrent_output(path, *args, **kwargs):
            result = write_text(path, *args, **kwargs)
            if path.name == 'binding-update.json':
                output.mkdir()
            return result
        with mock.patch.object(Path, 'write_text', concurrent_output):
            with self.assertRaises(FileExistsError):
                self.tool.prepare(output)
        self.assertEqual(list(output.iterdir()), [])
        self.assertEqual(list(output.parent.glob('.prepared.*')), [])

    def test_existing_output_is_refused_before_checkpoint_access(self):
        output = self.root / 'prepared'
        output.mkdir()
        with mock.patch.object(self.tool, 'verify_checkpoint') as checkpoint:
            with self.assertRaises(FileExistsError):
                self.tool.prepare(output)
            checkpoint.assert_not_called()
        self.assertEqual(list(output.iterdir()), [])

    @unittest.skipUnless(os.name == 'posix', 'POSIX directory mode check')
    def test_prepared_output_keeps_process_umask(self):
        output = self.root / 'prepared'
        previous = os.umask(0o027)
        try:
            self.tool.prepare(output)
        finally:
            os.umask(previous)
        self.assertEqual(output.stat().st_mode & 0o777, 0o750)


if __name__ == '__main__':
    unittest.main()
