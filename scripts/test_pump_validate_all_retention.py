"""The aggregate Pump corpus must not publish a partial retained suite set."""
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_validate_all as runner
import deep_disassembly as publisher


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PumpValidateAllRetentionTests(unittest.TestCase):
    def setUp(self):
        self.suites = [
            ('first', 'pump_validate_volume.py'),
            ('second', 'pump_validate_admin.py'),
            *runner.SUITES[2:],
        ]
        # Keep the current producer counts, including changes to later suites.
        # Only the first two suite names are replaced by publication fixtures.
        self.expected = dict(runner.EXPECTED_CASES)
        self.expected['first'] = self.expected.pop('volume')
        self.expected['second'] = self.expected.pop('administration')
        self.patches = [
            mock.patch.object(runner, 'SUITES', self.suites),
            mock.patch.object(runner, 'EXPECTED_CASES', self.expected),
            mock.patch.object(runner, 'CASE_COMPARE_KEYS', {
                **runner.CASE_COMPARE_KEYS, 'first': ('error',), 'second': ('error',),
            }),
            mock.patch.object(runner, 'pin_program', side_effect=lambda path: path),
            mock.patch.object(
                runner, 'audit_diagnostics',
                return_value={'mismatches': [], 'log_bearing_cases': 0}),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def invoke(self, output, candidate, original, run_suite):
        # These are publication-unit-test inputs only. The real compiler/VM
        # reproduction separately authenticates genuine producer receipts.
        for name in ('build-comparison.json', 'build-attempt.json'):
            path = candidate.parent / name
            if not path.exists():
                path.write_text('{}\n', encoding='utf-8')
        argv = [
            str(Path(runner.__file__)),
            '--candidate', str(candidate),
            '--output', str(output),
        ]
        def compiler(command, **kwargs):
            result = run_suite(command, **kwargs)
            return subprocess.CompletedProcess(command, result.returncode, ''), False
        with mock.patch.object(sys, 'argv', argv), \
                mock.patch.object(runner, 'run_suite_process', side_effect=compiler):
            return runner.main()

    def result(self, candidate, original, name):
        count = self.expected[name]
        if name == 'quote_control':
            return {
                'bound_inputs_sha256': {
                    runner.bound_input_key(candidate, runner.ROOT): sha(candidate),
                    runner.bound_input_key(original, runner.ROOT): sha(original),
                },
                'cases': count,
                'compare_keys': list(runner.QUOTE_CONTROL_COMPARE_KEYS),
                'results': [
                    {'case': f'fixture/{index}', 'matches': True, 'different_fields': [],
                     'original': dict.fromkeys(runner.QUOTE_CONTROL_COMPARE_KEYS),
                     'candidate': dict.fromkeys(runner.QUOTE_CONTROL_COMPARE_KEYS)}
                    for index in range(count)
                ],
            }
        if name == 'multi_hop_curve_partial':
            return {
                'candidate_sha256': sha(candidate),
                'original_pump_sha256': sha(original),
                'passed': count,
                'case_count': count,
                'cases': [{'mismatches': []}] * count,
            }
        if name == 'tokenkeg_two_curve':
            return {
                'candidate_sha256': sha(candidate),
                'provenance': {
                    'repository_inputs': {
                        'evidence/original/pump/deployed.so': sha(original),
                    },
                },
                'inputs_unchanged': True,
                'case_count': count,
                'original_successes': 16,
                'original_pump_cpi_cases': 18,
                'verified_outer_signatures': 40,
                'cases': [
                    {'candidate': {}, 'mismatches': []}
                ] * count,
            }
        def outcome():
            # Publication fixtures must retain the shapes required by the
            # maintained comparison contracts, including normalized diagnostics.
            return {
                **dict.fromkeys(runner.CASE_COMPARE_KEYS[name]),
                'metadata': {'return_data': None, 'inner_instructions': []},
                'logs': [],
                'relevant_logs': ['Program log: panicked at fixture.rs:1:1\nfixture panic'],
            }
        return {
            'original_sha256': sha(original),
            'candidate_sha256': sha(candidate),
            'case_count': count,
            'cases': [
                {'original': outcome(), 'candidate': outcome(),
                 'different_fields': [], 'expected_message': 'fixture panic'}
            ] * count,
            'mismatches': [],
        }

    def test_second_suite_failure_publishes_no_retained_subset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            output = root / 'aggregate/report.json'
            retained = output.parent / (output.name + '.suites')

            def run_suite(command, **_kwargs):
                result_path = Path(command[command.index('--output') + 1])
                if result_path.stem == 'first':
                    result_path.write_text(json.dumps(
                        self.result(candidate, original, 'first')))
                    return mock.Mock(returncode=0)
                raise RuntimeError('injected second suite failure')

            with self.assertRaisesRegex(
                    RuntimeError, 'injected second suite failure'):
                self.invoke(output, candidate, original, run_suite)

            self.assertFalse(
                retained.exists(),
                'failed corpus published an incomplete retained suite set')
            self.assertEqual(
                list(retained.parent.glob('.' + retained.name + '.staging-*')),
                [],
            )

    def test_complete_corpus_publishes_both_outputs_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            output = root / 'aggregate/report.json'
            retained = output.parent / (output.name + '.suites')

            def run_suite(command, **_kwargs):
                result_path = Path(command[command.index('--output') + 1])
                name = result_path.stem
                result_path.write_text(json.dumps(
                    self.result(candidate, original, name)))
                return mock.Mock(returncode=0)

            self.assertFalse(
                self.invoke(output, candidate, original, run_suite))

            self.assertTrue(output.is_file())
            retained_names = {path.name for path in retained.iterdir()}
            self.assertEqual(len(retained_names), 44)
            self.assertIn('first.json.gz', retained_names)
            self.assertIn('second.json.gz', retained_names)
            report = json.loads(output.read_bytes())
            self.assertEqual(report['case_count'], sum(self.expected.values()))
            self.assertEqual(report['process_runner_sha256'], {runner.bound_input_key(path, runner.ROOT): sha(path) for path in runner.PROCESS_INPUTS})
            self.assertEqual(set(report['suites']), set(self.expected))
            self.assertEqual(
                list(retained.parent.glob('.' + retained.name + '.staging-*')),
                [],
            )

    def test_existing_retained_set_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            output = root / 'aggregate/report.json'
            retained = output.parent / (output.name + '.suites')
            retained.mkdir(parents=True)
            marker = retained / 'prior.json.gz'
            marker.write_bytes(b'prior complete set')

            with self.assertRaises(FileExistsError):
                self.invoke(
                    output, candidate, original,
                    lambda *_args, **_kwargs: self.fail('suite unexpectedly ran'))

            self.assertEqual(marker.read_bytes(), b'prior complete set')
            self.assertFalse(output.exists())
            self.assertEqual(
                list(retained.parent.glob('.' + retained.name + '.staging-*')),
                [],
            )

    def complete_suites(self, candidate, original):
        def run(command, **_kwargs):
            path = Path(command[command.index('--output') + 1])
            path.write_text(json.dumps(self.result(candidate, original, path.stem)))
            return mock.Mock(returncode=0)
        return run

    def test_late_report_collision_preserves_complete_recovery_and_new_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            output = root / 'aggregate/report.json'
            retained = output.parent / (output.name + '.suites')
            link = os.link
            def late_writer(source, destination):
                (retained / 'late-user-file').write_bytes(b'late evidence')
                output.write_bytes(b'other writer report')
                return link(source, destination)
            with mock.patch.object(runner.os, 'link', late_writer):
                with self.assertRaises(FileExistsError):
                    self.invoke(output, candidate, original, self.complete_suites(candidate, original))
            self.assertEqual(output.read_bytes(), b'other writer report')
            self.assertEqual((retained / 'late-user-file').read_bytes(), b'late evidence')
            self.assertEqual(len(list(retained.glob('*.json.gz'))), len(self.suites))
            reports = list(output.parent.glob('.report.json.staging-*/report.json'))
            self.assertEqual(len(reports), 1)
            self.assertEqual(set(json.loads(reports[0].read_bytes())['suites']), set(self.expected))

    @unittest.skipUnless(os.name == 'posix', 'POSIX permission check')
    def test_complete_outputs_keep_normal_umask_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            output = root / 'aggregate/report.json'
            previous = os.umask(0o027)
            try:
                self.invoke(output, candidate, original, self.complete_suites(candidate, original))
            finally:
                os.umask(previous)
            self.assertEqual(output.stat().st_mode & 0o777, 0o640)
            self.assertEqual((output.parent / (output.name + '.suites')).stat().st_mode & 0o777, 0o750)

    def test_late_retained_destination_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            output = root / 'aggregate/report.json'
            retained = output.parent / (output.name + '.suites')
            rename = publisher.rename_directory
            def late_writer(source, destination, **kwargs):
                retained.mkdir()
                (retained / 'late-user-file').write_bytes(b'late evidence')
                return rename(source, destination, **kwargs)
            with mock.patch.object(publisher, 'rename_directory', late_writer):
                with self.assertRaises(FileExistsError):
                    self.invoke(output, candidate, original, self.complete_suites(candidate, original))
            self.assertEqual((retained / 'late-user-file').read_bytes(), b'late evidence')
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob('.report.json.staging-*')), [])

    def test_input_aliases_are_rejected_before_running_suites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            hardlink = root / 'hardlink.json'
            os.link(candidate, hardlink)
            symlink = root / 'symlink.json'
            symlink.symlink_to(candidate)
            for output in (candidate, hardlink, symlink):
                with self.subTest(output=output.name), self.assertRaisesRegex(
                        ValueError, 'output aliases a bound input'):
                    self.invoke(output, candidate, original,
                                lambda *_a, **_k: self.fail('suite launched for an input alias'))
                self.assertEqual(candidate.read_bytes(), b'candidate')
                self.assertFalse((root / (output.name + '.suites')).exists())


    def test_pinned_two_curve_dispatch_retains_original_receipt_location(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            pinned = root / 'private-snapshot' / 'program.so'
            pinned.parent.mkdir()
            pinned.write_bytes(candidate.read_bytes())
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            output = root / 'aggregate/report.json'
            complete = self.complete_suites(pinned, original)
            seen = []

            def child(command, **kwargs):
                self.assertEqual(Path(command[command.index('--candidate') + 1]), pinned)
                path = Path(command[command.index('--output') + 1])
                if path.stem == 'tokenkeg_two_curve':
                    self.assertIn('--build-report', command)
                    self.assertEqual(Path(command[command.index('--build-report') + 1]),
                                     (candidate.parent / 'build-comparison.json').resolve())
                    seen.append(path.stem)
                return complete(command, **kwargs)

            with mock.patch.object(runner, 'pin_program', return_value=pinned):
                self.assertFalse(self.invoke(output, candidate, original, child))
            self.assertEqual(seen, ['tokenkeg_two_curve'])
            report = json.loads(output.read_bytes())
            for name in ('build-comparison.json', 'build-attempt.json'):
                source = candidate.parent / name
                self.assertEqual(report['build_inputs_sha256'][runner.bound_input_key(source, runner.ROOT)], sha(source))

    def test_real_pinning_keeps_public_candidate_in_output_admission(self):
        from pump_amm_reusable_harness import pin_program
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            alias = root / 'candidate-alias.json'; os.link(candidate, alias)
            for destination in (candidate, alias):
                with self.subTest(destination=destination), mock.patch.object(runner, 'pin_program', side_effect=pin_program):
                    with self.assertRaisesRegex(ValueError, 'output aliases a bound input'):
                        self.invoke(destination, candidate, original,
                            lambda *_a, **_k: self.fail('suite ran before public input admission'))
                    self.assertEqual(candidate.read_bytes(), b'candidate')

    def test_changed_producer_receipt_cannot_publish_complete_corpus(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate')
            original = runner.ROOT / 'evidence/original/pump/deployed.so'
            output = root / 'aggregate/report.json'
            complete = self.complete_suites(candidate, original)

            def child(command, **kwargs):
                result = complete(command, **kwargs)
                (root / 'build-comparison.json').write_text('{"changed":true}\n', encoding='utf-8')
                return result

            with self.assertRaisesRegex(AssertionError, 'build receipt changed during execution'):
                self.invoke(output, candidate, original, child)
            self.assertFalse(output.exists())
            self.assertFalse((output.parent / (output.name + '.suites')).exists())

if __name__ == '__main__':
    unittest.main()
