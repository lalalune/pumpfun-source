#!/usr/bin/env python3
"""Failure-atomicity tests for the macOS frontier replay packet."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock

import pump_validate_parallel as validator
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'reviewed_frontier_replay', HERE / 'pump_replay_macos_frontier.py')
frontier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frontier)


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ReplayPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='frontier-replay-')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.input = self.root / 'work/pump-macos-frontier-inputs'
        self.build = self.root / 'work/pump-macos-qualification/candidate'
        self.output = self.root / 'work/pump-macos-frontier-runtime/evidence'
        self.failures = self.output.parent / 'failures'
        frontier.ROOT = self.root
        frontier.INPUT = self.input
        frontier.BUILD = self.build
        frontier.OUT = self.output
        self.fixture()

    def write_gzip(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(gzip.compress(payload, mtime=0))

    def write_json_gzip(self, path, payload):
        self.write_gzip(path, json.dumps(payload).encode())

    def fixture(self):
        self.source_files = {
            'Cargo.toml': b'[workspace]\nmembers=["programs/pump"]\nresolver="2"\n',
            'Cargo.lock': b'version = 3\n',
            'programs/pump/Cargo.toml': b'[package]\nname="replay-fixture"\nversion="0.1.0"\nedition="2021"\n',
            'programs/pump/src/lib.rs': b'pub fn retained() -> u64 { 42 }\n',
        }
        candidate = b'synthetic candidate'
        self.record = {
            'returncode': 0,
            'source_unchanged': True,
            'comparison': {'candidate_sha256': digest(candidate)},
            'source_sha256': {
                'work/pump-macos-qualification/candidate/source/' + name: digest(data)
                for name, data in self.source_files.items()
            },
        }
        archive = self.input / 'candidate/compiled-source.tar.gz'
        archive.parent.mkdir(parents=True)
        with tarfile.open(archive, 'w:gz') as bundle:
            for name, data in self.source_files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                bundle.addfile(member, io.BytesIO(data))
        names = {
            'candidate.so': candidate,
            'unstripped.so': b'synthetic unstripped candidate',
            'build-comparison.json': json.dumps(self.record).encode(),
            'build-attempt.json': b'{"status":"passed"}\n',
        }
        for name, data in names.items():
            self.write_gzip(self.input / 'candidate' / (name + '.gz'), data)
        (self.input / 'revision.txt').write_text('synthetic-revision\n')
        self.seal_inputs()

    def seal_inputs(self):
        manifest = {
            path.relative_to(self.input).as_posix(): digest(path.read_bytes())
            for path in sorted(self.input.rglob('*')) if path.is_file() and path.name != 'MANIFEST.json'
        }
        (self.input / 'MANIFEST.json').write_text(json.dumps(manifest))

    def validate_sources(self, command):
        comparison = Path(command[command.index('--build-comparison') + 1])
        record = json.loads(comparison.read_text())
        crate = Path(command[command.index('--source-directory') + 1])
        candidate = Path(command[command.index('--candidate') + 1])
        with mock.patch.object(validator, 'ROOT', self.root):
            sources, inputs, _ = validator.validate_build_sources(record, crate, candidate)
        self.assertTrue(all(digest((self.root / name).read_bytes()) == value
                            for name, value in sources.items()))
        original = comparison.parent / 'build-comparison.json'
        self.assertIn(original, inputs, 'original receipt is not protected during runtime')
        self.assertEqual(json.loads(original.read_text()), self.record)
        self.assertEqual(record['replay_source_binding']['origin_build_record_sha256'], digest(original.read_bytes()))
        return sources

    def successful_run(self, command, **kwargs):
        output = Path(command[command.index('--output') + 1])
        candidate_sha256 = digest(b'synthetic candidate')
        if any('pump_validate_parallel.py' in str(part) for part in command):
            self.validate_sources(command)
            self.write_json_gzip(output, {
                'candidate_sha256': candidate_sha256,
                'suites': [{}] * 44,
                'case_count': sum(validator.base.EXPECTED_CASES.values()),
                'mismatches': [],
                'diagnostics': {
                    'mismatches': [],
                    'log_bearing_cases': sum(validator.base.EXPECTED_CASES.values()) - 4,
                },
            })
        elif any('pump_buyback_recipient_differential.py' in str(part) for part in command):
            output.write_text(json.dumps({
                'candidate_sha256': candidate_sha256,
                'case_count': 42,
                'mismatches': [],
            }))
        else:
            count = 20 if any(
                'pump_migration_quote_differential.py' in str(part)
                for part in command) else 40
            self.write_json_gzip(output, {
                'candidate_sha256': candidate_sha256,
                'case_count': count,
                'mismatches': [],
                'diagnostics': {
                    'mismatches': [],
                    'log_bearing_cases': count,
                },
            })
        return subprocess.CompletedProcess(command, 0)

    def test_failed_suite_does_not_publish_final_paths_and_can_retry(self):
        calls = []

        def fail(command, **kwargs):
            calls.append(command)
            self.validate_sources(command)
            raise subprocess.CalledProcessError(17, command)

        with mock.patch.object(frontier.subprocess, 'run', side_effect=fail):
            for attempt in (1, 2):
                with self.assertRaises(subprocess.CalledProcessError):
                    frontier.main()
                self.assertFalse(self.build.exists(), 'failed replay published BUILD')
                self.assertFalse(self.output.exists(), 'failed replay published OUT')
                attempts = sorted(self.failures.iterdir())
                self.assertEqual(len(attempts), attempt)
                state = json.loads((attempts[-1] / 'failure.json').read_text())
                self.assertEqual(state['status'], 'failed')
                self.assertEqual(state['error_type'], 'CalledProcessError')
                self.assertTrue((attempts[-1] / 'evidence/native-input-binding.json').is_file())
                self.assertFalse((attempts[-1] / 'evidence/qualification.json').exists())
        self.assertEqual(len(calls), 2)

    def test_success_publishes_only_the_complete_packet(self):
        with mock.patch.object(frontier.subprocess, 'run', side_effect=self.successful_run):
            frontier.main()
        self.assertTrue((self.build / 'candidate.so').is_file())
        self.assertEqual(
            json.loads((self.output / 'qualification.json').read_text())['status'],
            'passed')
        self.assertEqual(
            json.loads((self.output / 'qualification.json').read_text())['corpus_cases'],
            sum(validator.base.EXPECTED_CASES.values()))
        self.assertTrue((self.output / 'MANIFEST.json').is_file())
        self.assertFalse(self.failures.exists())
        self.assertEqual(list(self.build.parent.glob('.candidate-*')), [])
        self.assertEqual(list(self.output.parent.glob('.evidence-*')), [])

    def test_changed_archived_source_is_rejected_before_validator(self):
        archive = self.input / 'candidate/compiled-source.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            for name, data in self.source_files.items():
                if name.endswith('.rs'):
                    data += b'pub fn changed() {}\n'
                item = tarfile.TarInfo(name)
                item.size = len(data)
                bundle.addfile(item, io.BytesIO(data))
        self.seal_inputs()
        with mock.patch.object(frontier.subprocess, 'run') as run:
            with self.assertRaisesRegex(AssertionError, 'restored compiler input differs'):
                frontier.main()
        run.assert_not_called()
        self.assertFalse(self.build.exists())

    def test_extra_archived_rust_input_is_rejected_by_actual_validator(self):
        self.source_files['programs/pump/src/extra.rs'] = b'pub fn extra() {}\n'
        with tarfile.open(self.input / 'candidate/compiled-source.tar.gz', 'w:gz') as bundle:
            for name, data in self.source_files.items():
                item = tarfile.TarInfo(name)
                item.size = len(data)
                bundle.addfile(item, io.BytesIO(data))
        self.seal_inputs()
        with mock.patch.object(frontier.subprocess, 'run', side_effect=self.successful_run):
            with self.assertRaisesRegex(AssertionError, 'source binding omits or changes compiler inputs'):
                frontier.main()
        self.assertFalse(self.build.exists())

    def test_repository_config_keeps_its_original_binding(self):
        config = self.root / '.cargo/config.toml'
        config.parent.mkdir()
        config.write_bytes(b'[build]\njobs=1\n')
        self.record['source_sha256']['.cargo/config.toml'] = digest(config.read_bytes())
        self.write_json_gzip(self.input / 'candidate/build-comparison.json.gz', self.record)
        self.seal_inputs()
        with mock.patch.object(frontier.subprocess, 'run', side_effect=self.successful_run):
            frontier.main()
        replay_record = json.loads((self.build / 'replay-build-comparison.json').read_text())
        self.assertEqual(replay_record['source_sha256']['.cargo/config.toml'], digest(config.read_bytes()))

    def test_changed_origin_receipt_is_rejected_by_actual_validator(self):
        def change_origin(command, **kwargs):
            comparison = Path(command[command.index('--build-comparison') + 1])
            original = comparison.parent / 'build-comparison.json'
            original.write_bytes(original.read_bytes() + b'\n')
            return self.successful_run(command, **kwargs)

        with mock.patch.object(frontier.subprocess, 'run', side_effect=change_origin):
            with self.assertRaisesRegex(AssertionError, 'replay source origin hash'):
                frontier.main()
        self.assertFalse(self.build.exists())

    def test_derived_receipt_cannot_change_original_build_fields(self):
        def change_derived(command, **kwargs):
            comparison = Path(command[command.index('--build-comparison') + 1])
            record = json.loads(comparison.read_text())
            record['target'] = 'changed-after-relocation'
            comparison.write_text(json.dumps(record))
            return self.successful_run(command, **kwargs)

        with mock.patch.object(frontier.subprocess, 'run', side_effect=change_derived):
            with self.assertRaisesRegex(AssertionError, 'replay changed original build fields'):
                frontier.main()
        self.assertFalse(self.build.exists())

    def test_derived_receipt_cannot_coerce_original_json_types(self):
        self.record['workspace_layout'] = True
        self.write_json_gzip(self.input / 'candidate/build-comparison.json.gz', self.record)
        self.seal_inputs()
        for field, value in (('workspace_layout', 1), ('returncode', False), ('source_unchanged', 1)):
            with self.subTest(field=field):
                def change_type(command, **kwargs):
                    comparison = Path(command[command.index('--build-comparison') + 1])
                    record = json.loads(comparison.read_text())
                    record[field] = value
                    comparison.write_text(json.dumps(record))
                    return self.successful_run(command, **kwargs)

                with mock.patch.object(frontier.subprocess, 'run', side_effect=change_type):
                    with self.assertRaisesRegex(AssertionError, 'replay changed original build fields'):
                        frontier.main()
                self.assertFalse(self.build.exists())

    def test_stale_corpus_total_cannot_publish(self):
        def stale_total(command, **kwargs):
            result = self.successful_run(command, **kwargs)
            if any('pump_validate_parallel.py' in str(part) for part in command):
                output = Path(command[command.index('--output') + 1])
                report = json.loads(gzip.decompress(output.read_bytes()))
                report['case_count'] = 10468
                report['diagnostics']['log_bearing_cases'] = 10464
                self.write_json_gzip(output, report)
            return result

        with mock.patch.object(frontier.subprocess, 'run', side_effect=stale_total):
            with self.assertRaises(AssertionError):
                frontier.main()
        self.assertFalse(self.build.exists())
        self.assertFalse(self.output.exists())

    def test_relocation_binding_paths_must_be_relative_and_confined(self):
        for field in ('origin_build_record', 'original_workspace_prefix', 'execution_workspace_prefix'):
            for value in ('../outside', str(self.root / 'absolute')):
                with self.subTest(field=field, value=value):
                    def change_path(command, **kwargs):
                        comparison = Path(command[command.index('--build-comparison') + 1])
                        record = json.loads(comparison.read_text())
                        record['replay_source_binding'][field] = value
                        comparison.write_text(json.dumps(record))
                        return self.successful_run(command, **kwargs)

                    with mock.patch.object(frontier.subprocess, 'run', side_effect=change_path):
                        with self.assertRaisesRegex(AssertionError, 'replay binding path must be repository-relative'):
                            frontier.main()
                    self.assertFalse(self.build.exists())


if __name__ == '__main__':
    unittest.main()
