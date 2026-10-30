"""Retained successes require typed claims, distinct cases and matching promised fields."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pump_validate_all as base
import pump_validate_parallel as parallel

# This is the comparison list emitted by the maintained QuoteControl producer.
KEYS = ['error', 'before_accounts', 'after_accounts', 'rollback', 'event_payloads',
        'inner_instructions', 'return_data', 'transaction_base64',
        'signature_verification', 'blockhash', 'sigverify_enabled', 'blockhash_check_enabled']


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
