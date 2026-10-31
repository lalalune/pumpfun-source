"""Retained successes require typed claims, distinct cases and matching promised fields."""
import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pump_validate_all as base
import pump_validate_parallel as parallel

# This is the comparison list emitted by the maintained QuoteControl producer.
KEYS = ['error', 'before_accounts', 'after_accounts', 'rollback', 'event_payloads',
        'inner_instructions', 'return_data', 'transaction_base64',
        'signature_verification', 'blockhash', 'sigverify_enabled', 'blockhash_check_enabled']


class CapturedAdministrativeReceiptContract(unittest.TestCase):
    """Exercise admission with the real producer and retained local program."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(__file__).resolve().parents[1]
        cls.artifact = root / 'evidence/original/pump/deployed.so'
        output = Path(cls.temporary.name) / 'administration.json'
        subprocess.run([sys.executable, '-B', str(root / 'scripts/pump_validate_admin.py'),
                        '--candidate', str(cls.artifact), '--output', str(output)],
                       cwd=root, capture_output=True, text=True, check=True, timeout=60)
        cls.report = json.loads(output.read_bytes())

    def validate(self, report):
        base.validate_case_results(report, 'administration')
        return parallel.validate_result('administration', report, self.artifact, self.artifact)

    def test_producer_receipt_is_admitted(self):
        self.assertEqual(self.report['case_count'], 93)
        self.assertEqual(self.report['mismatches'], [])
        self.assertEqual(self.validate(self.report), 93)

    def test_retained_error_balance_and_bytes_must_match(self):
        for field, changed in [('error', 'unexpected failure'), ('lamports', 1), ('data_hex', 'ff')]:
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                report['cases'][0]['candidate'][field] = changed
                with self.assertRaisesRegex(AssertionError, 'retained comparison contradicts'):
                    self.validate(report)

    def test_removing_a_promised_field_cannot_preserve_success(self):
        for field in ('error', 'lamports', 'data_hex'):
            for sides in [('original',), ('candidate',), ('original', 'candidate')]:
                with self.subTest(field=field, sides=sides):
                    report = copy.deepcopy(self.report)
                    for side in sides:
                        del report['cases'][0][side][field]
                    with self.assertRaisesRegex(AssertionError, 'compared field .* missing'):
                        self.validate(report)

    def test_incidental_diagnostics_are_not_promised_equal(self):
        report = copy.deepcopy(self.report)
        report['cases'][0]['candidate']['logs'].append('Program log: incidental diagnostic')
        report['cases'][0]['original']['compute_units'] = 1
        report['cases'][0]['candidate']['compute_units'] = 2
        self.assertEqual(self.validate(report), 93)

    def test_every_generic_suite_has_a_comparison_contract(self):
        specialized = {'quote_control', 'multi_hop_curve_partial', 'tokenkeg_two_curve'}
        self.assertEqual(set(base.CASE_COMPARE_KEYS), set(base.EXPECTED_CASES) - specialized)


class CapturedExtendedReceiptContract(unittest.TestCase):
    """Recheck nested semantics and normalized diagnostics in actual VM receipts."""

    @classmethod
    def setUpClass(cls):
        from concurrent.futures import ThreadPoolExecutor
        import gzip
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        root = Path(__file__).resolve().parents[1]
        cls.artifact = root / 'evidence/original/pump/deployed.so'
        names = {'creator_collection', 'minimum_distribution', 'fee_sweeps',
                 'incentive_schedule', 'claim_panic_diagnostics'}
        def produce(item):
            name, filename = item
            output = Path(cls.temporary.name) / (name + '.json')
            command = base.suite_command(name, root / 'scripts' / filename, cls.artifact,
                                         output, root / 'programs/pump', None)
            subprocess.run(command, cwd=root, capture_output=True, text=True,
                           check=True, timeout=180)
            raw = output.read_bytes()
            return name, json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        with ThreadPoolExecutor(max_workers=5) as pool:
            cls.reports = dict(pool.map(produce, [(n, f) for n, f in base.SUITES if n in names]))

    def changed(self, suite, index=0):
        report = self.reports[suite].copy()
        report['cases'] = report['cases'].copy()
        report['cases'][index] = copy.deepcopy(report['cases'][index])
        return report

    def validate(self, suite, report):
        base.validate_case_results(report, suite)
        return parallel.validate_result(suite, report, self.artifact, self.artifact)

    def test_actual_producer_receipts_are_admitted(self):
        for suite, report in self.reports.items():
            with self.subTest(suite=suite):
                self.assertEqual(self.validate(suite, report), base.EXPECTED_CASES[suite])

    def test_boolean_and_numeric_values_do_not_coerce(self):
        report = self.changed('creator_collection')
        self.assertIs(report['cases'][0]['original']['signature_verification'][0], True)
        report['cases'][0]['candidate']['signature_verification'][0] = 1
        with self.assertRaisesRegex(AssertionError, 'signature_verification'):
            self.validate('creator_collection', report)
        report = self.changed('creator_collection')
        value = report['cases'][0]['original']['payer_lamports']
        self.assertIs(type(value), int)
        report['cases'][0]['candidate']['payer_lamports'] = float(value)
        with self.assertRaisesRegex(AssertionError, 'payer_lamports'):
            self.validate('creator_collection', report)

    def test_nested_metadata_cannot_disappear_or_change(self):
        for suite in ('minimum_distribution', 'fee_sweeps'):
            for field in ('return_data', 'inner_instructions'):
                for sides in [('original',), ('candidate',), ('original', 'candidate')]:
                    with self.subTest(suite=suite, field=field, sides=sides):
                        report = self.changed(suite)
                        for side in sides:
                            del report['cases'][0][side]['metadata'][field]
                        with self.assertRaisesRegex(AssertionError, 'compared field .* missing'):
                            self.validate(suite, report)
                report = self.changed(suite)
                report['cases'][0]['candidate']['metadata'][field] = {'changed': True}
                with self.assertRaisesRegex(AssertionError, 'metadata\\.'):
                    self.validate(suite, report)

    def test_event_logs_are_required_but_incidental_logs_are_allowed(self):
        report = self.changed('fee_sweeps')
        report['cases'][0]['candidate']['logs'].append('Program data: changed')
        with self.assertRaisesRegex(AssertionError, 'event_logs'):
            self.validate('fee_sweeps', report)
        report = self.changed('fee_sweeps')
        report['cases'][0]['candidate']['logs'].append('Program log: incidental diagnostic')
        report['cases'][0]['candidate']['metadata']['compute_units_consumed'] = 999999
        self.assertEqual(self.validate('fee_sweeps', report), base.EXPECTED_CASES['fee_sweeps'])

    def test_transaction_identity_remains_required(self):
        for suite in ('incentive_schedule', 'claim_panic_diagnostics'):
            report = self.changed(suite)
            report['cases'][0]['candidate']['transaction_base64'] += 'changed'
            with self.assertRaisesRegex(AssertionError, 'transaction_base64'):
                self.validate(suite, report)

    def test_schedule_diagnostics_ignore_coordinates_and_keep_semantics(self):
        suite = 'incentive_schedule'
        report = self.changed(suite)
        report['cases'][0]['candidate']['logs'].extend([
            'Program log: panicked at candidate.rs:7:9\nretained message',
            'Program log: AnchorError thrown in candidate.rs:7. Error Code: Test. Error Number: 6000. Error Message: retained message',
            'Program log: Left: 12', 'Program log: Right: 13'])
        report['cases'][0]['original']['logs'].extend([
            'Program log: panicked at original.rs:1:2\nretained message',
            'Program log: AnchorError thrown in original.rs:1. Error Code: Test. Error Number: 6000. Error Message: retained message',
            'Program log: Left: 12', 'Program log: Right: 13'])
        self.assertEqual(self.validate(suite, report), base.EXPECTED_CASES[suite])
        for index in range(-4, 0):
            changed = copy.deepcopy(report)
            changed['cases'][0]['candidate']['logs'][index] += 'changed'
            with self.subTest(index=index), self.assertRaisesRegex(AssertionError, 'panic_messages|anchor_diagnostics'):
                self.validate(suite, changed)

    def test_claim_panic_is_complete_unique_and_matches_expected(self):
        suite = 'claim_panic_diagnostics'
        report = self.changed(suite)
        logs = report['cases'][0]['candidate']['relevant_logs']
        index = next(i for i, line in enumerate(logs) if line.startswith('Program log: panicked at '))
        message = logs[index].split('\n', 1)[1]
        logs[index] = 'Program log: panicked at other.rs:88:1\n' + message
        self.assertEqual(self.validate(suite, report), 2)
        for change in ('missing', 'empty', 'duplicate', 'malformed', 'changed', 'expected'):
            changed = copy.deepcopy(report)
            outcome = changed['cases'][0]['candidate']
            if change == 'missing':
                del outcome['relevant_logs']
            elif change == 'empty':
                outcome['relevant_logs'] = []
            elif change == 'duplicate':
                outcome['relevant_logs'].append(outcome['relevant_logs'][index])
            elif change == 'malformed':
                outcome['relevant_logs'][index] = 'Program log: panicked at no complete message'
            elif change == 'changed':
                outcome['relevant_logs'][index] += 'changed'
            else:
                changed['cases'][0]['expected_message'] += 'changed'
            with self.subTest(change=change), self.assertRaises(AssertionError):
                self.validate(suite, changed)


def quote_rows(count):
    return [{'case': f'fixture/{index}', 'matches': True, 'different_fields': [],
             'original': {**dict.fromkeys(KEYS), 'compute_units': 1},
             'candidate': {**dict.fromkeys(KEYS), 'compute_units': 2}}
            for index in range(count)]


class RetainedReceiptContract(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.artifact = Path(temporary.name).resolve() / 'program.so'
        self.artifact.write_bytes(b'fixture')
        self.report = {'bound_inputs_sha256': {str(self.artifact): base.sha(self.artifact)},
                       'cases': 507, 'results': quote_rows(507), 'compare_keys': KEYS,
                       'mismatches': 0}

    def validate(self, report=None):
        return parallel.validate_result('quote_control', report or self.report,
                                        self.artifact, self.artifact)

    def test_valid_protocol_keeps_incidental_compute_differences(self):
        self.assertEqual(self.validate(), 507)

    def test_success_is_a_boolean_not_a_truthy_claim(self):
        for value in ['false', 'true', 1, [], {}]:
            with self.subTest(value=value):
                report = copy.deepcopy(self.report)
                report['results'][0]['matches'] = value
                with self.assertRaises(AssertionError):
                    self.validate(report)

    def test_counts_are_actual_integers(self):
        report = copy.deepcopy(self.report)
        report['cases'] = 507.0
        with self.assertRaises(AssertionError):
            self.validate(report)
        for value in [True, 1.0, '1']:
            with self.subTest(value=value), self.assertRaises(AssertionError):
                base.retained_case_count({'cases': [{}], 'case_count': value})

    def test_repeating_a_case_cannot_replace_an_omitted_scenario(self):
        self.report['results'][-1] = copy.deepcopy(self.report['results'][0])
        with self.assertRaisesRegex(AssertionError, 'duplicate'):
            self.validate()

    def test_missing_scenario_id_is_rejected(self):
        del self.report['results'][0]['case']
        with self.assertRaises(AssertionError):
            self.validate()

    def test_empty_difference_claim_cannot_contradict_paired_outcomes(self):
        for field in KEYS:
            with self.subTest(field=field):
                report = copy.deepcopy(self.report)
                report['results'][0]['candidate'][field] = 'changed'
                with self.assertRaisesRegex(AssertionError, 'comparison'):
                    self.validate(report)

    def test_missing_compared_fields_or_weakened_compare_keys_are_rejected(self):
        for missing in [False, True]:
            with self.subTest(missing=missing):
                report = copy.deepcopy(self.report)
                if missing:
                    del report['results'][0]['candidate']['error']
                else:
                    report['compare_keys'] = ['error']
                with self.assertRaises(AssertionError):
                    self.validate(report)

    def test_two_curve_success_and_counts_are_typed(self):
        report = {'candidate_sha256': 'candidate',
                  'provenance': {'repository_inputs': {'evidence/original/pump/deployed.so': 'original'}},
                  'inputs_unchanged': True, 'case_count': 20, 'original_successes': 16,
                  'original_pump_cpi_cases': 18, 'verified_outer_signatures': 40,
                  'cases': [{'candidate': {}, 'mismatches': []} for _ in range(20)]}
        self.assertEqual(base.validate_two_curve(report, 'candidate', 'original'), 20)
        for key, value in [('inputs_unchanged', 'false'), ('case_count', 20.0),
                           ('original_successes', 16.0), ('verified_outer_signatures', 40.0)]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                base.validate_two_curve(report | {key: value}, 'candidate', 'original')


    def test_partial_curve_counts_are_typed(self):
        digest = base.sha(self.artifact)
        report = {'candidate_sha256': digest, 'original_pump_sha256': digest,
                  'passed': 56, 'case_count': 56, 'cases': [{'mismatches': []} for _ in range(56)]}
        self.assertEqual(parallel.validate_result('multi_hop_curve_partial', report,
                                                  self.artifact, self.artifact), 56)
        for key in ['passed', 'case_count']:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                parallel.validate_result('multi_hop_curve_partial', report | {key: 56.0},
                                         self.artifact, self.artifact)

    def test_loader_success_flags_and_sizes_are_typed(self):
        path = self.artifact.with_name('loader.json')
        row = {'elf_sha256': base.sha(self.artifact), 'program_bytes': 36,
               'program_owner': 'BPFLoaderUpgradeab1e11111111111111111111111',
               'programdata_bytes': 10485760, 'elf_prefix_unchanged': True,
               'zero_allocation_tail': True}
        receipt = {'loads': [row], 'harness': str(self.artifact),
                   'input_sha256': {str(self.artifact): base.sha(self.artifact)}}
        path.write_text(json.dumps(receipt))
        parallel.validate_loader_receipt('fixture', path, self.artifact,
                                          self.artifact, self.artifact, [])
        for key, value in [('program_bytes', 36.0), ('programdata_bytes', 10485760.0),
                           ('elf_prefix_unchanged', 'false'), ('zero_allocation_tail', 1)]:
            with self.subTest(key=key), self.assertRaises(AssertionError):
                path.write_text(json.dumps(receipt | {'loads': [row | {key: value}]}))
                parallel.validate_loader_receipt('fixture', path, self.artifact,
                                                  self.artifact, self.artifact, [])


if __name__ == '__main__':
    unittest.main()
