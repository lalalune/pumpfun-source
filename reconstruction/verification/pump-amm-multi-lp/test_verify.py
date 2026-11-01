#!/usr/bin/env python3
"""Case-bound, fully resealed controls for the finite multi-LP reader."""
from __future__ import annotations
import base64
import builtins
import copy
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import py_compile
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
from solders.compute_budget import set_compute_unit_limit
from solders.hash import Hash
from solders.transaction import Transaction

import verify
lifecycle = verify.L
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def mutate_u64(record, offset, value):
    raw = bytearray(base64.b64decode(record["data_base64"]))
    struct = __import__('struct')
    struct.pack_into("<Q", raw, offset, value)
    record["data_base64"] = base64.b64encode(raw).decode()
    record["data_sha256"] = hashlib.sha256(raw).hexdigest()
    if offset == 64:
        record["token_amount"] = value
    elif offset == 36:
        record["mint_supply"] = value
    elif offset == 203:
        record["pool_lp_supply"] = value


def transaction_metadata(receipt, transaction):
    receipt.update(transaction_base64=base64.b64encode(bytes(transaction)).decode(),
                   signatures=[str(v) for v in transaction.signatures],
                   message_sha256=lifecycle.sha(bytes(transaction.message)),
                   blockhash=str(transaction.message.recent_blockhash),
                   blockhash_sha256=lifecycle.sha(bytes(transaction.message.recent_blockhash)),
                   signer_pubkeys=[str(v) for v in transaction.message.account_keys[:transaction.message.header.num_required_signatures]])


class VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = lifecycle.CAPTURED["original"]
        # Exactly one bounded original control; readers below send zero tx.
        cls.report = lifecycle.run_suite(cls.candidate)
        problems = verify.verify(cls.report, cls.candidate)
        if problems:
            raise AssertionError("Positive fixture must validate before any negative control: " + repr(problems))

    def assert_refused(self, mutation):
        report = copy.deepcopy(self.report)
        mutation(report)
        self.assertTrue(verify.verify(report, self.candidate))

    def test_valid_original_control(self):
        self.assertEqual(verify.verify(self.report, self.candidate), [])

    def test_retained_historical_summary_stays_bound_without_upgrading_v1(self):
        root = HERE / 'qualification'
        summary = json.loads((root / 'summary.json').read_bytes())
        self.assertEqual(lifecycle.file_sha(root / 'report.json.gz'), summary['report_sha256'])
        historical = verify.read(root / 'report.json.gz')
        self.assertEqual(historical['case_count'], summary['cases'])
        self.assertEqual(historical['program_sha256']['candidate'], summary['candidate_sha256'])
        self.assertTrue(verify.verify(historical, self.candidate))

    def test_signature_substitution(self):
        self.assert_refused(lambda r: r['cases'][0]['original']['receipts'][0]['signatures'].__setitem__(0, 'forged'))

    def test_lp_supply_corruption(self):
        def mutate(r):
            row = r['cases'][0]
            value = row['original']['receipts'][-1]['after'][row['fixture']['lp_mint']]
            mutate_u64(value, 36, value['mint_supply'] + 1)
        self.assert_refused(mutate)

    def test_provider_balance_corruption(self):
        def mutate(r):
            row = r['cases'][0]
            value = row['original']['receipts'][-1]['after'][row['fixture']['provider_a_accounts']['base']]
            mutate_u64(value, 64, value['token_amount'] + 1)
        self.assert_refused(mutate)

    def test_pool_reserve_corruption(self):
        def mutate(r):
            row = r['cases'][0]
            value = row['original']['receipts'][-1]['after'][row['fixture']['vault_base']]
            mutate_u64(value, 64, value['token_amount'] + 1)
        self.assert_refused(mutate)

    def test_incorrect_owner(self):
        def mutate(r):
            row = r['cases'][0]
            for side in ('original', 'candidate'):
                row[side]['receipts'][-1]['after'][row['fixture']['provider_a_accounts']['lp']]['owner'] = str(lifecycle.SYSTEM)
        self.assert_refused(mutate)

    def test_missing_transaction(self):
        self.assert_refused(lambda r: r['cases'][0]['original']['receipts'].pop())

    def test_altered_event(self):
        self.assert_refused(lambda r: r['cases'][0]['original']['receipts'][2]['events'].append('Program data: dGFtcGVy'))

    def test_altered_error(self):
        self.assert_refused(lambda r: r['cases'][3]['original']['receipts'][-1].__setitem__('error', None))

    def test_forged_passing_count(self):
        self.assert_refused(lambda r: r['classification_counts'].__setitem__('equal_observed_behavior', 999))

    def test_changed_executable_input(self):
        self.assertTrue(verify.verify(self.report, lifecycle.CAPTURED['spl_token']))

    def test_changed_declared_source_inputs(self):
        self.assert_refused(lambda r: r['candidate_source_sha256'].__setitem__('programs/pump-amm/src/lib.rs', '0' * 64))

    def test_duplicate_transaction_identity(self):
        def mutate(r):
            row = r['cases'][0]
            for side in ('original', 'candidate'):
                first, second = row[side]['receipts'][:2]
                for field in ('transaction_base64', 'signatures', 'message_sha256', 'blockhash', 'blockhash_sha256', 'signer_pubkeys'):
                    second[field] = copy.deepcopy(first[field])
        self.assert_refused(mutate)

    def test_corrupted_account_encoding(self):
        def mutate(r):
            row = r['cases'][0]
            row['original']['receipts'][0]['after'][row['fixture']['base_mint']]['data_base64'] = 'not-base64'
        self.assert_refused(mutate)

    def test_partial_signature_vector_with_valid_remaining_signature_is_rejected(self):
        def mutate(r):
            for side in ('original', 'candidate'):
                receipt = r['cases'][0][side]['receipts'][0]
                tx = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64']))
                self.assertEqual(tx.message.header.num_required_signatures, 2)
                partial = Transaction.populate(tx.message, tx.signatures[:1])
                self.assertEqual(partial.verify_with_results(), [True])
                transaction_metadata(receipt, partial)
        self.assert_refused(mutate)

    def test_signed_transaction_with_trailing_wire_bytes_is_rejected(self):
        def mutate(r):
            for side in ('original', 'candidate'):
                receipt = r['cases'][0][side]['receipts'][0]
                raw = base64.b64decode(receipt['transaction_base64']) + b'garbage'
                decoded = Transaction.from_bytes(raw)
                self.assertTrue(all(decoded.verify_with_results()))
                self.assertNotEqual(bytes(decoded), raw)
                receipt['transaction_base64'] = base64.b64encode(raw).decode()
        self.assert_refused(mutate)

    def test_validly_signed_unrelated_message_is_rejected_after_metadata_reseal(self):
        def mutate(r):
            for side in ('original', 'candidate'):
                receipt = r['cases'][0][side]['receipts'][0]
                old = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64']))
                changed = Transaction.new_signed_with_payer([set_compute_unit_limit(100000)], lifecycle.FEE_PAYER.pubkey(),
                                                            [lifecycle.FEE_PAYER], old.message.recent_blockhash)
                self.assertEqual(changed.verify_with_results(), [True])
                transaction_metadata(receipt, changed)
        self.assert_refused(mutate)

    def test_extra_valid_instruction_is_rejected(self):
        def mutate(r):
            plan = lifecycle.plans()[0]
            harness = lifecycle.fixture_only(self.candidate, 0, plan)
            _, instructions, signers, _ = lifecycle.plan_step(harness, plan['steps'][0], 0)
            for side in ('original', 'candidate'):
                receipt = r['cases'][0][side]['receipts'][0]
                old = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64']))
                changed = Transaction.new_signed_with_payer([*instructions, set_compute_unit_limit(100000)],
                                                            lifecycle.FEE_PAYER.pubkey(), signers, old.message.recent_blockhash)
                self.assertTrue(all(changed.verify_with_results()))
                transaction_metadata(receipt, changed)
        self.assert_refused(mutate)

    def test_valid_signatures_with_wrong_fixture_blockhash_are_rejected(self):
        def mutate(r):
            plan = lifecycle.plans()[0]
            harness = lifecycle.fixture_only(self.candidate, 0, plan)
            _, instructions, signers, _ = lifecycle.plan_step(harness, plan['steps'][0], 0)
            changed = Transaction.new_signed_with_payer(instructions, lifecycle.FEE_PAYER.pubkey(), signers, Hash.new_unique())
            self.assertTrue(all(changed.verify_with_results()))
            for side in ('original', 'candidate'):
                transaction_metadata(r['cases'][0][side]['receipts'][0], changed)
        self.assert_refused(mutate)

    def test_foreign_initial_payer_state_cannot_reseal_both_sides(self):
        def mutate(r):
            row = r['cases'][0]
            for side in ('original', 'candidate'):
                for receipt in row[side]['receipts']:
                    for phase in ('before', 'after'):
                        receipt[phase][row['fixture']['fee_payer']]['lamports'] += 1
        self.assert_refused(mutate)

    def test_omitted_watch_key_cannot_reseal_both_sides(self):
        def mutate(r):
            for side in ('original', 'candidate'):
                for receipt in r['cases'][0][side]['receipts']:
                    for phase in ('before', 'after'):
                        del receipt[phase][str(lifecycle.EVENT)]
        self.assert_refused(mutate)

    def test_cross_step_discontinuity_is_rejected(self):
        def mutate(r):
            row = r['cases'][0]
            for side in ('original', 'candidate'):
                receipt = row[side]['receipts'][1]
                receipt['before'][row['fixture']['fee_payer']]['lamports'] += 1
                receipt['accounting'] = verify.accounting(receipt['before'], receipt['after'], row['fixture'])
        self.assert_refused(mutate)

    def test_resealed_fee_payer_lamport_creation_is_rejected(self):
        def mutate(r):
            row = r['cases'][0]
            payer = row['fixture']['fee_payer']
            for side in ('original', 'candidate'):
                for number, receipt in enumerate(row[side]['receipts']):
                    if number:
                        receipt['before'][payer]['lamports'] += 1
                    receipt['after'][payer]['lamports'] += 1
                    receipt['accounting'] = verify.accounting(receipt['before'], receipt['after'], row['fixture'])
        self.assert_refused(mutate)

    def test_integer_flags_and_coerced_counts_are_rejected(self):
        mutations = [lambda r: [r['cases'][3][s]['receipts'][-1].__setitem__('rollback_nonfee_equal', 1) for s in ('original', 'candidate')],
                     lambda r: [r['cases'][0][s]['receipts'][2].__setitem__('instruction_count', True) for s in ('original', 'candidate')],
                     lambda r: r['classification_counts'].__setitem__('different_behavior', False),
                     lambda r: r.__setitem__('transaction_count_per_image', float(r['transaction_count_per_image']))]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                self.assert_refused(mutate)

    def test_changed_error_string_cannot_hide_behind_cached_outcome(self):
        def mutate(r):
            for side in ('original', 'candidate'):
                r['cases'][3][side]['receipts'][-1]['error'] = 'invented-but-cached-outcome-retained'
        self.assert_refused(mutate)

    def test_raw_token_mint_role_cannot_be_resealed(self):
        def mutate(r):
            row = r['cases'][0]
            address = row['fixture']['provider_a_accounts']['lp']
            for side in ('original', 'candidate'):
                for receipt in row[side]['receipts']:
                    for phase in ('before', 'after'):
                        record = receipt[phase][address]
                        if record is not None:
                            raw = bytearray(base64.b64decode(record['data_base64']))
                            raw[:32] = bytes(lifecycle.SYSTEM)
                            record['data_base64'] = base64.b64encode(raw).decode()
                            record['data_sha256'] = lifecycle.sha(raw)
        self.assert_refused(mutate)

    def test_self_sealed_source_build_claim_is_rejected(self):
        self.assert_refused(lambda r: r.__setitem__('candidate_build', {'kind': 'source_build', 'receipt': {}, 'receipt_canonical_sha256': lifecycle.canonical_hash({})}))

    def test_non_elf_candidate_cannot_be_declared_as_supplied_runtime_binary(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'not-an-elf.so'
            candidate.write_bytes(b'deliberate negative fixture, never executed')
            report = copy.deepcopy(self.report)
            report['program_sha256']['candidate'] = lifecycle.file_sha(candidate)
            self.assertTrue(verify.verify(report, candidate))

    def test_image_path_mutation_does_not_change_immutable_reader_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            shutil.copyfile(self.candidate, candidate)
            original = lifecycle.fixture_only
            changed = []
            def mutation(*args, **kwargs):
                if not changed:
                    candidate.write_bytes(candidate.read_bytes() + b'tamper')
                    changed.append(True)
                return original(*args, **kwargs)
            with mock.patch.object(lifecycle, 'fixture_only', side_effect=mutation):
                problems = verify.verify(self.report, candidate)
            self.assertTrue(changed)
            self.assertIn('images_changed_during_verification', problems)


class SourceAndCliAdmissionTests(unittest.TestCase):
    def test_cli_replay_keeps_historical_git_context_separate_from_observations(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            report = {'upstream_commit': 'a' * 40, 'observation': {'exact': 7}}
            path.write_text(json.dumps(report))
            for changed in (False, True):
                replayed = {'upstream_commit': 'b' * 40, 'observation': {'exact': 8 if changed else 7}}
                output = io.StringIO()
                with self.subTest(changed_observation=changed), \
                        mock.patch.object(sys, 'argv', ['verify.py', '--report', str(path), '--candidate', 'unused.so', '--replay']), \
                        mock.patch.object(verify, 'verify', return_value=[]), \
                        mock.patch.object(lifecycle, 'run_suite', return_value=replayed), \
                        contextlib.redirect_stdout(output):
                    status = verify.main()
                result = json.loads(output.getvalue())
                self.assertEqual(status, changed)
                self.assertEqual(result['report_upstream_commit'], 'a' * 40)
                self.assertEqual(result['replay_upstream_commit'], 'b' * 40)
                self.assertEqual(result['deterministic_replay_equal'], not changed)
                self.assertEqual(result['verified'], not changed)

    def cohort(self, root):
        for relative in verify.A.snapshot_inputs():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        return root / HERE.relative_to(ROOT)

    def private_reader(self, directory, *, imports=None):
        loader = types.ModuleType('_private_lp_loader')
        loader.__file__ = str(directory / 'admission.py')
        raw = Path(loader.__file__).read_bytes()
        loader.__source_sha256__ = lifecycle.sha(raw)
        exec(compile(raw, loader.__file__, 'exec', dont_inherit=True), loader.__dict__)
        return loader.source_module('verify', directory / 'verify.py', imports=imports,
                                    bindings={'_ADMISSION': loader})

    def test_canonical_alias_poison_does_not_replace_raw_graph(self):
        names = ('lifecycle', 'admission', 'pump_differential_output')
        prior = {name: sys.modules.get(name) for name in names}
        fake = {name: types.ModuleType(name) for name in names}
        sys.modules.update(fake)
        try:
            with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
                loaded = self.private_reader(self.cohort(Path(temporary)))
                self.assertTrue(callable(loaded.L.plan_step))
                for name in names:
                    self.assertIs(sys.modules[name], fake[name])
        finally:
            for name, value in prior.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value

    def test_loaded_json_byte_change_is_rejected_before_fixture_construction(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            loaded = self.private_reader(self.cohort(Path(temporary)))
            path = loaded.L.IDL_PATH
            path.write_bytes(path.read_bytes() + b'\n')
            with mock.patch.object(loaded.L, 'fixture_only', side_effect=AssertionError('must not construct fixture')):
                problems = loaded.verify({}, loaded.L.CAPTURED['original'])
            self.assertTrue(any('executed source/data differs' in item for item in problems), problems)

    def test_executable_timestamp_caches_are_ignored_by_actual_reader_cli(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = self.cohort(Path(temporary))
            markers = []
            for name in ('lifecycle', 'admission'):
                path = directory / (name + '.py')
                clean = path.read_bytes()
                marker = Path(temporary) / (name + '-cache-executed')
                markers.append(marker)
                malicious = ('from pathlib import Path\nPath(' + repr(str(marker)) + ").write_text('bad')\n").encode()
                malicious += b'#' * (len(clean) - len(malicious))
                self.assertEqual(len(clean), len(malicious))
                path.write_bytes(malicious)
                os.utime(path, (1700000000, 1700000000))
                py_compile.compile(str(path), doraise=True)
                path.write_bytes(clean)
                os.utime(path, (1700000000, 1700000000))
                spec = importlib.util.spec_from_file_location('_executable_lp_cache_control', path)
                cached = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cached)
                self.assertTrue(marker.exists(), 'standard loader must prove cache executable')
                marker.unlink()
            result = subprocess.run([sys.executable, '-I', '-B', str(directory / 'verify.py'), '--help'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(any(marker.exists() for marker in markers))
            self.assertIn('usage:', result.stdout)

    def test_optimized_reader_exits_before_imports_or_argument_admission(self):
        for flags in (['-O'], ['-OO']):
            result = subprocess.run([sys.executable, '-I', '-B', *flags, str(HERE / 'verify.py'), '--not-a-valid-argument'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Normal Python is required', result.stderr)
            self.assertNotIn('usage:', result.stderr)

    def test_duplicate_keys_nonfinite_and_symlink_reports_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'report.json'
            for raw in (b'{"cases":[],"cases":[]}', b'{"value":NaN}', b'{"value":1e999}'):
                path.write_bytes(raw)
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    verify.read(path)
            link = Path(temporary) / 'link.json'
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                verify.read(link)


if __name__ == '__main__':
    unittest.main()
