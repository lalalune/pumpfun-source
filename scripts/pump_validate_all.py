#!/usr/bin/env python3
"""Run the published 44-suite bounded Pump corpus against one compiled ELF.

Publish the complete retained-suite directory atomically, then link the report.
If a late report destination prevents the second publication, keep the complete
suite directory and staged report for recovery. The two paths are not a single
filesystem transaction.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from pump_diagnostic_audit import audit as audit_diagnostics
from pump_diagnostic_audit import bound_input_key
from pump_amm_reusable_harness import pin_program

ROOT = Path(__file__).resolve().parents[1]
from serial_suite_process import PROCESS_INPUTS, run_suite_process, validate_timeout

DEFAULT_SUITE_TIMEOUT = 1800.0
SUITES = [('volume', 'pump_validate_volume.py'), ('administration', 'pump_validate_admin.py'), ('authority', 'pump_validate_authority.py'), ('configuration', 'pump_validate_config_admin.py'), ('buy', 'pump_validate_buy.py'), ('sell', 'pump_validate_sell.py'), ('quote', 'pump_validate_quote.py'), ('creator_collection', 'pump_creator_collect_differential.py'), ('creator_distribution', 'pump_creator_distribution_differential.py'), ('minimum_distribution', 'pump_minimum_fee_differential.py'), ('creator_collection_v2', 'pump_creator_collect_v2_differential.py'), ('extension', 'pump_extend_differential.py'), ('volume_sync', 'pump_volume_sync_differential.py'), ('fee_sweeps', 'pump_fee_sweep_differential.py'), ('creator_migration', 'pump_creator_migration_differential.py'), ('admin_cto', 'pump_admin_cto_differential.py'), ('set_params', 'pump_set_params_differential.py'), ('set_creator', 'pump_set_creator_differential.py'), ('idl_authority', 'pump_idl_authority_differential.py'), ('legacy_create', 'pump_create_differential.py'), ('exact_quote_v3', 'pump_exact_quote_differential.py'), ('create_v2', 'pump_create_quote_differential.py'), ('legacy_sell', 'pump_legacy_sell_differential.py'), ('legacy_sell_configured_fee', 'pump_legacy_sell_configured_fee_differential.py'), ('sell_v2', 'pump_sell_v2_differential.py'), ('create_control', 'pump_create_control_differential.py'), ('migration', 'pump_migrate_differential.py'), ('v3_configured_fee', 'pump_v3_configured_fee_differential.py'), ('legacy_buy', 'pump_legacy_buy_differential.py'), ('buy_v2', 'pump_buy_v2_differential.py'), ('migrate_v2', 'pump_migrate_v2_differential.py'), ('cashback', 'pump_cashback_differential.py'), ('global_init', 'pump_global_init_differential.py'), ('holder_distribution', 'pump_holder_distribution_differential.py'), ('nested_create', 'pump_create_nested_differential.py'), ('quote_control', 'pump_quote_control_fresh_differential.py'), ('multi_hop_curve_partial', 'research/pump-multi-hop-corpus/harness.py')]
EXPECTED_CASES = {'volume': 66, 'administration': 93, 'creator_collection_v2': 154, 'extension': 308, 'exact_quote_v3': 352, 'sell_v2': 206, 'legacy_buy': 284, 'migrate_v2': 827, 'global_init': 40, 'buy': 334, 'creator_collection': 119, 'creator_distribution': 298, 'admin_cto': 388, 'set_params': 169, 'legacy_create': 87, 'migration': 228, 'holder_distribution': 649, 'multi_hop_curve_partial': 56, 'authority': 59, 'configuration': 351, 'sell': 301, 'minimum_distribution': 181, 'creator_migration': 139, 'set_creator': 509, 'legacy_sell': 115, 'legacy_sell_configured_fee': 28, 'v3_configured_fee': 372, 'cashback': 283, 'quote': 130, 'volume_sync': 341, 'fee_sweeps': 504, 'idl_authority': 171, 'create_v2': 297, 'create_control': 85, 'buy_v2': 216, 'nested_create': 48, 'quote_control': 507}

SUITES.append(('tokenkeg_two_curve', 'pump_tokenkeg_two_curve_differential.py'))
EXPECTED_CASES['tokenkeg_two_curve'] = 20
SUITES.append(('incentive_claim', 'pump_claim_boundary_differential.py'))
EXPECTED_CASES['incentive_claim'] = 334
SUITES.append(('virtual_reserve_sync', 'pump_virtual_reserve_differential.py'))
EXPECTED_CASES['virtual_reserve_sync'] = 192
SUITES.append(('claim_panic_diagnostics', 'pump_claim_panic_differential.py'))
EXPECTED_CASES['claim_panic_diagnostics'] = 2
SUITES.append(('incentive_schedule', 'pump_incentive_schedule_differential.py'))
EXPECTED_CASES['incentive_schedule'] = 575

SUITES.append(('earned_cashback', 'pump_earned_cashback_differential.py'))
EXPECTED_CASES['earned_cashback'] = 61

SUITES.append(('legacy_cashback', 'pump_legacy_cashback_differential.py'))
EXPECTED_CASES['legacy_cashback'] = 14

def validate_two_curve(result, candidate_sha, original_sha):
    assert result['candidate_sha256'] == candidate_sha
    assert result['provenance']['repository_inputs']['evidence/original/pump/deployed.so'] == original_sha
    assert result['inputs_unchanged'] is True
    for key in ('case_count', 'original_successes', 'original_pump_cpi_cases', 'verified_outer_signatures'):
        assert type(result[key]) is int, f'{key} must be an integer'
    assert result['case_count'] == len(result['cases']) == 20
    assert result['original_successes'] == 16 and result['original_pump_cpi_cases'] == 18
    assert result['verified_outer_signatures'] == 40
    assert all(row['candidate'] is not None and row['mismatches'] == [] for row in result['cases'])
    return 20

def retained_case_count(result):
    """Bind a reported count to the retained JSON case array, not just a claim."""
    cases = result.get('cases')
    assert isinstance(cases, list), 'a retained cases array is required'
    count = result.get('case_count', len(cases))
    assert type(count) is int, 'case_count must be an integer'
    assert count == len(cases), ('case_count differs from retained cases', count, len(cases))
    return count


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protect_inputs(destinations, inputs):
    """Reject path, symlink and existing hardlink aliases before output writes."""
    protected = {Path(path).resolve() for path in inputs}
    existing = [path for path in protected if path.exists()]
    for destination in destinations:
        resolved = destination.resolve()
        if resolved in protected or (resolved.exists() and any(
                resolved.samefile(path) for path in existing)):
            raise ValueError('validation output aliases a bound input: ' + str(destination))


def validate_quote_control(result, candidate, original):
    bound = result['bound_inputs_sha256']
    assert bound[bound_input_key(candidate, ROOT)] == sha(candidate)
    assert bound[bound_input_key(original, ROOT)] == sha(original)
    count = result['cases']
    assert type(count) is int, 'cases must be an integer'
    assert isinstance(result['results'], list), 'results must be a list'
    assert count == len(result['results'])
    assert result['compare_keys'] == list(QUOTE_CONTROL_COMPARE_KEYS), 'comparison fields differ'
    identities = set()
    for row in result['results']:
        identity = row.get('case')
        assert isinstance(identity, str) and identity, 'case identity missing'
        assert identity not in identities, f'duplicate quote-control case: {identity}'
        identities.add(identity)
        assert row['matches'] is True and row['different_fields'] == []
        assert all(isinstance(row.get(side), dict) for side in ('original', 'candidate'))
        assert all(key in row['original'] and key in row['candidate'] and
                   row['original'][key] == row['candidate'][key]
                   for key in QUOTE_CONTROL_COMPARE_KEYS), f'{identity}: retained comparison contradicts success'
    return count


QUOTE_CONTROL_COMPARE_KEYS = ('error', 'before_accounts', 'after_accounts', 'rollback',
                             'event_payloads', 'inner_instructions', 'return_data',
                             'transaction_base64', 'signature_verification', 'blockhash',
                             'sigverify_enabled', 'blockhash_check_enabled')


CASE_DIFFERENCE_FIELDS = ('different_fields', 'diff', 'differences', 'mismatched_fields')


# These are the direct semantic fields compared by each maintained producer.
# Nested metadata and normalized diagnostics are projected below; incidental
# raw logs and compute usage remain outside the comparison contract.
# QuoteControl and the two specialized multi-hop receipts have separate gates.
CASE_COMPARE_KEYS = {
    'volume': ('error', 'account', 'payer_lamports', 'user_lamports', 'events', 'inner_instructions'),
    'administration': ('error', 'data_hex', 'lamports'),
    'creator_collection': ('transaction_base64', 'signature_verification', 'error', 'account',
                           'creator', 'payer_lamports', 'events', 'inner_instructions'),
    'quote': ('error', 'accounts', 'event_payloads', 'inner'),
    'minimum_distribution': ('error', 'before', 'after', 'events'),
    'fee_sweeps': ('error', 'before', 'after'),
    'legacy_cashback': ('error', 'before', 'accounts', 'events', 'inner', 'return_data'),
    'virtual_reserve_sync': ('error', 'before', 'after', 'events', 'inner', 'return_data'),
    **dict.fromkeys(('authority', 'configuration'),
                    ('error', 'data_hex', 'lamports', 'payer_lamports', 'authority_lamports',
                     'event_payloads', 'inner_instructions')),
    **dict.fromkeys(('buy', 'sell'), ('error', 'accounts', 'event_payloads', 'inner_instructions')),
    **dict.fromkeys(('exact_quote_v3', 'v3_configured_fee'),
                    ('error', 'accounts', 'inner_instructions', 'event_payloads', 'return_data')),
    **dict.fromkeys(('creator_collection_v2', 'set_params'),
                    ('error', 'before', 'after', 'events', 'inner', 'returns')),
    **dict.fromkeys(('incentive_claim', 'claim_panic_diagnostics'),
                    ('error', 'before', 'after', 'event_data_base64', 'inner', 'transaction_base64')),
    **dict.fromkeys(('legacy_sell', 'legacy_sell_configured_fee', 'sell_v2', 'legacy_buy',
                     'buy_v2', 'cashback', 'global_init', 'earned_cashback'),
                    ('error', 'accounts', 'events', 'inner', 'return_data')),
    **dict.fromkeys(('creator_distribution', 'extension', 'volume_sync', 'creator_migration',
                     'admin_cto', 'set_creator', 'idl_authority', 'legacy_create', 'create_v2',
                     'create_control', 'migration', 'migrate_v2', 'holder_distribution',
                     'nested_create', 'incentive_schedule'),
                    ('error', 'before', 'after', 'events', 'inner', 'return')),
}
CASE_COMPARE_KEYS['virtual_reserve_sync'] += ('transaction_base64',)
CASE_COMPARE_KEYS['incentive_schedule'] += ('transaction_base64',)


def same_json_value(left, right):
    """Compare retained values without Python's bool/int or int/float coercion."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(same_json_value(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(same_json_value(a, b) for a, b in zip(left, right))
    return left == right


def compared_outcome(outcome, suite, index):
    """Project exactly the direct, nested and normalized producer comparisons."""
    def field(name):
        value = outcome
        for part in name.split('.'):
            assert isinstance(value, dict) and part in value, \
                f'{suite} case {index}: compared field {name} missing'
            value = value[part]
        return value

    def logs(name='logs'):
        value = field(name)
        assert isinstance(value, list) and all(isinstance(line, str) for line in value), \
            f'{suite} case {index}: compared field {name} must contain log strings'
        return value

    values = {name: field(name) for name in CASE_COMPARE_KEYS[suite]}
    if suite in ('minimum_distribution', 'fee_sweeps'):
        for name in ('metadata.return_data', 'metadata.inner_instructions'):
            values[name] = field(name)
    if suite == 'fee_sweeps':
        values['event_logs'] = [line for line in logs() if line.startswith('Program data: ')]
    if suite in ('cashback', 'earned_cashback', 'legacy_cashback', 'incentive_schedule'):
        lines = logs()
        values['panic_messages'] = [line.split('\n', 1)[-1] for line in lines
                                    if line.startswith('Program log: panicked at ')]
        if suite == 'legacy_cashback':
            values['anchor_diagnostics'] = [match.groups() for line in lines if (match := re.search(
                r'Error Code: (.*?)\. Error Number: (\d+)\. Error Message: (.*)', line))]
        if suite == 'incentive_schedule':
            values['anchor_diagnostics'] = [re.sub(r' thrown in .*?:\d+\.', '.', line)
                                            for line in lines if line.startswith((
                                                'Program log: AnchorError', 'Program log: Left:',
                                                'Program log: Right:'))]
    if suite == 'claim_panic_diagnostics':
        panics = [line for line in logs('relevant_logs') if line.startswith('Program log: panicked at ')]
        assert len(panics) == 1 and '\n' in panics[0], \
            f'{suite} case {index}: exactly one complete panic diagnostic is required'
        values['panic_message'] = panics[0].split('\n', 1)[1]
    return values


def validate_case_results(result, suite):
    """Recompare promised fields as well as checking the retained success claims."""
    assert suite in CASE_COMPARE_KEYS, f'unknown comparison contract: {suite}'
    assert isinstance(result['cases'], list), 'case results must be a list'
    for index, row in enumerate(result['cases']):
        assert isinstance(row, dict), f'case {index}: result must be an object'
        assert isinstance(row.get('original'), dict), f'case {index}: original outcome missing'
        assert isinstance(row.get('candidate'), dict), f'case {index}: candidate outcome missing'
        fields = [name for name in CASE_DIFFERENCE_FIELDS if name in row]
        assert fields or 'match' in row, f'case {index}: comparison result missing'
        if 'match' in row:
            assert row['match'] is True, f'case {index}: match is not true'
        for name in fields:
            assert row[name] == [], f'case {index}: {name} is not an empty difference list'
        original = compared_outcome(row['original'], suite, index)
        candidate = compared_outcome(row['candidate'], suite, index)
        for field in original:
            assert same_json_value(original[field], candidate[field]), \
                f'{suite} case {index}: retained comparison contradicts success for {field}'
        if suite == 'claim_panic_diagnostics':
            assert isinstance(row.get('expected_message'), str), f'{suite} case {index}: expected panic message missing'
            assert original['panic_message'] == row['expected_message'], \
                f'{suite} case {index}: retained panic contradicts expected message'


def publish_file(staged, output):
    """Publish without replacement; return whether staging was consumed.

    Rename on Windows, link elsewhere.

    Windows sandboxes refuse hard links (WinError 5). The sibling staging
    directory is on the same filesystem. Windows rename refuses an existing
    destination; reporting whether it consumed the file preserves ownership
    when cleaning up the staging directory.
    """
    if os.name == "nt":
        os.rename(staged, output)
        return True
    os.link(staged, output)
    return False


def suite_command(name, script, candidate, output, source_directory, build_report):
    """Keep the pinned ELF and the actual producer receipt separate."""
    command = [sys.executable, str(script), '--candidate', str(candidate), '--output', str(output)]
    source_text = script.read_text()
    if "'--source-directory'" in source_text or '"--source-directory"' in source_text:
        command += ['--source-directory', str(source_directory.resolve())]
    if name == 'tokenkeg_two_curve':
        command += ['--build-report', str(build_report)]
    return command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-directory', type=Path, default=ROOT / 'programs/pump')
    parser.add_argument('--build-report', type=Path,
                        help='Actual producer build-comparison.json; defaults beside the selected candidate')
    parser.add_argument('--suite-timeout', type=float, default=DEFAULT_SUITE_TIMEOUT,
                        help='Seconds per suite; POSIX timeouts terminate its process group')
    args = parser.parse_args()
    validate_timeout(args.suite_timeout)
    source_paths = [path for path in args.source_directory.rglob('*')
                    if path.is_file() and 'target' not in path.relative_to(args.source_directory).parts
                    and (path.suffix == '.rs' or path.name in ('Cargo.toml', 'Cargo.lock'))]
    if not source_paths:
        raise SystemExit(f'no Rust/Cargo inputs under {args.source_directory}')
    candidate_input = args.candidate.resolve()
    build_report = (args.build_report or candidate_input.parent / 'build-comparison.json').resolve()
    build_attempt = build_report.with_name('build-attempt.json')
    build_inputs = (build_report, build_attempt)
    candidate = pin_program(candidate_input)
    original = ROOT / 'evidence/original/pump/deployed.so'
    runner = Path(__file__).resolve()
    candidate_sha, original_sha, runner_sha = map(sha, (candidate, original, runner))
    process_hashes = {path: sha(path) for path in PROCESS_INPUTS}
    suites, scripts = {}, {}
    assert len(SUITES) == len(EXPECTED_CASES) == len({name for name, _ in SUITES}) == 44
    assert {name for name, _ in SUITES} == set(EXPECTED_CASES)
    retained = args.output.parent / (args.output.name + '.suites')
    suite_paths = [ROOT / filename if filename.startswith(('repro/', 'research/'))
                   else ROOT / 'scripts' / filename for _, filename in SUITES]
    protect_inputs([args.output, *(retained / (name + '.json.gz') for name, _ in SUITES)],
                   [candidate_input, candidate, original, runner, *build_inputs, *PROCESS_INPUTS,
                    ROOT / 'scripts/pump_diagnostic_audit.py',
                    *suite_paths, *source_paths])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for destination in (args.output, retained):
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
    build_inputs = {path: sha(path) for path in build_inputs}
    from deep_disassembly import rename_directory, temporary_sibling
    retained_staging = report_directory = None
    published_retained = preserve_recovery = report_consumed = report_published = False
    report_identity = None
    try:
        retained_staging = temporary_sibling(retained, 'staging')
        report_directory = temporary_sibling(args.output, 'staging')
        report_staging = report_directory / 'report.json'
        with tempfile.TemporaryDirectory(prefix='pump-differential-') as tmp:
            for name, filename in SUITES:
                script = ROOT / filename if filename.startswith(('repro/', 'research/')) else ROOT / 'scripts' / filename
                before = sha(script)
                output = Path(tmp) / (name + '.json')
                command = suite_command(name, script, candidate, output,
                                        args.source_directory, build_report)
                completed, timed_out = run_suite_process(command, cwd=ROOT, timeout=args.suite_timeout)
                if completed.stdout:
                    print(completed.stdout, end='', flush=True)
                if timed_out:
                    raise SystemExit(f'suite {name} exceeded {args.suite_timeout}s')
                completed.check_returncode()
                assert before == sha(script), f'harness changed during execution: {filename}'
                assert runner_sha == sha(runner), 'aggregate runner changed during execution'
                assert all(sha(path) == digest for path, digest in process_hashes.items()), 'suite process helper changed'
                assert candidate_sha == sha(candidate), 'candidate changed during execution'
                assert original_sha == sha(original), 'original changed during execution'
                assert all(sha(path) == digest for path, digest in build_inputs.items()), 'build receipt changed during execution'
                raw = output.read_bytes()
                result = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
                if name == 'quote_control':
                    count = validate_quote_control(result, candidate, original)
                elif name == 'multi_hop_curve_partial':
                    assert type(result['passed']) is type(result['case_count']) is int
                    assert result['candidate_sha256'] == candidate_sha
                    assert result['original_pump_sha256'] == original_sha
                    assert result['passed'] == result['case_count'] == 56
                    assert len(result['cases']) == 56
                    assert all(not row['mismatches'] for row in result['cases'])
                    count = result['case_count']
                elif name == 'tokenkeg_two_curve':
                    count = validate_two_curve(result, candidate_sha, original_sha)
                else:
                    assert result.get('original_sha256', result.get('provenance', {}).get(str(original))) == original_sha
                    assert result.get('candidate_sha256', result.get('provenance', {}).get(str(candidate))) == candidate_sha
                    count = retained_case_count(result)
                    validate_case_results(result, name)
                assert count == EXPECTED_CASES[name], (name, count, EXPECTED_CASES[name])
                assert not result.get('mismatches', result.get('failures', [])), name
                result['case_count'] = count
                suites[name] = result
                scripts[filename] = before
                (retained_staging / (name + '.json.gz')).write_bytes(
                    gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        assert sum(s['case_count'] for s in suites.values()) == sum(EXPECTED_CASES.values())
        diagnostics = audit_diagnostics(suites)
        report = {
            'scope': 'Published 44-suite bounded Pump differential corpus. Per-suite limits remain in receipts; not full source recovery or binary identity.',
            'original_sha256': original_sha, 'candidate_sha256': candidate_sha,
            'runner_sha256': runner_sha, 'script_sha256': scripts,
            'suite_timeout_seconds': args.suite_timeout,
            'process_runner_sha256': {bound_input_key(path, ROOT): digest for path, digest in process_hashes.items()},
            'build_inputs_sha256': {bound_input_key(path, ROOT): digest
                                    for path, digest in build_inputs.items()},
            'case_count': sum(s['case_count'] for s in suites.values()),
            'source_directory': str(args.source_directory.resolve()),
            'diagnostic_audit_sha256': sha(ROOT / 'scripts/pump_diagnostic_audit.py'),
            'diagnostics': diagnostics,
            'mismatches': diagnostics['mismatches'], 'suites': suites,
        }
        raw = (json.dumps(report, separators=(',', ':')) + '\n').encode()
        report_staging.write_bytes(
            gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
        report_stat = report_staging.stat()
        report_identity = (report_stat.st_dev, report_stat.st_ino)
        rename_directory(retained_staging, retained)
        published_retained = True
        try:
            report_consumed = publish_file(report_staging, args.output)
            report_published = True
        except BaseException as error:
            # The complete suite directory is already public. A late writer
            # may have added files: retain it and the complete report for
            # recovery instead of deleting a directory we no longer own.
            preserve_recovery = True
            error.add_note(f'Complete suites retained at {retained}; report retained at {report_staging}')
            raise
    finally:
        if retained_staging is not None and not published_retained:
            shutil.rmtree(retained_staging, ignore_errors=True)
        if report_directory is not None and not preserve_recovery:
            if report_published:
                if not report_consumed:
                    try:
                        current = report_staging.stat()
                        if (current.st_dev, current.st_ino) == report_identity:
                            report_staging.unlink()
                    except FileNotFoundError:
                        pass
                # Do not recursively remove paths a later writer now owns.
                try:
                    report_directory.rmdir()
                except OSError:
                    pass
            else:
                shutil.rmtree(report_directory, ignore_errors=True)
    print(json.dumps({'cases': report['case_count'], 'diagnostic_log_cases': diagnostics['log_bearing_cases'], 'mismatches': len(report['mismatches'])}))
    return bool(report['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
