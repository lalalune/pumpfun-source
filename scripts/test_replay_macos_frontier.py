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
        source = self.root / 'programs/pump/Cargo.toml'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'synthetic source\n')
        candidate = b'synthetic candidate'
        record = {
            'returncode': 0,
            'source_unchanged': True,
            'comparison': {'candidate_sha256': digest(candidate)},
            'source_sha256': {'programs/pump/Cargo.toml': digest(source.read_bytes())},
        }
        archive = self.input / 'candidate/compiled-source.tar.gz'
        archive.parent.mkdir(parents=True)
        with tarfile.open(archive, 'w:gz') as bundle:
            data = source.read_bytes()
            member = tarfile.TarInfo('programs/pump/Cargo.toml')
            member.size = len(data)
            bundle.addfile(member, io.BytesIO(data))
        names = {
            'candidate.so': candidate,
            'unstripped.so': b'synthetic unstripped candidate',
            'build-comparison.json': json.dumps(record).encode(),
            'build-attempt.json': b'{"status":"passed"}\n',
        }
        for name, data in names.items():
            self.write_gzip(self.input / 'candidate' / (name + '.gz'), data)
        (self.input / 'revision.txt').write_text('synthetic-revision\n')
        manifest = {
            path.relative_to(self.input).as_posix(): digest(path.read_bytes())
            for path in sorted(self.input.rglob('*')) if path.is_file()
        }
        (self.input / 'MANIFEST.json').write_text(json.dumps(manifest))

    def successful_run(self, command, **kwargs):
        output = Path(command[command.index('--output') + 1])
        candidate_sha256 = digest(b'synthetic candidate')
        if any('pump_validate_parallel.py' in str(part) for part in command):
            self.write_json_gzip(output, {
                'candidate_sha256': candidate_sha256,
                'suites': [{}] * 44,
                'case_count': 10468,
                'mismatches': [],
                'diagnostics': {
                    'mismatches': [],
                    'log_bearing_cases': 10464,
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
        self.assertTrue((self.output / 'MANIFEST.json').is_file())
        self.assertFalse(self.failures.exists())
        self.assertEqual(list(self.build.parent.glob('.candidate-*')), [])
        self.assertEqual(list(self.output.parent.glob('.evidence-*')), [])


if __name__ == '__main__':
    unittest.main()
