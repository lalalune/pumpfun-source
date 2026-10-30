#!/usr/bin/env python3
"""Run the published 44-suite bounded Pump corpus against one compiled ELF."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from pump_diagnostic_audit import audit as audit_diagnostics
from pump_diagnostic_audit import bound_input_key
from pump_amm_reusable_harness import pin_program

ROOT = Path(__file__).resolve().parents[1]
SUITES = [('volume', 'pump_validate_volume.py'), ('administration', 'pump_validate_admin.py'), ('authority', 'pump_validate_authority.py'), ('configuration', 'pump_validate_config_admin.py'), ('buy', 'pump_validate_buy.py'), ('sell', 'pump_validate_sell.py'), ('quote', 'pump_validate_quote.py'), ('creator_collection', 'pump_creator_collect_differential.py'), ('creator_distribution', 'pump_creator_distribution_differential.py'), ('minimum_distribution', 'pump_minimum_fee_differential.py'), ('creator_collection_v2', 'pump_creator_collect_v2_differential.py'), ('extension', 'pump_extend_differential.py'), ('volume_sync', 'pump_volume_sync_differential.py'), ('fee_sweeps', 'pump_fee_sweep_differential.py'), ('creator_migration', 'pump_creator_migration_differential.py'), ('admin_cto', 'pump_admin_cto_differential.py'), ('set_params', 'pump_set_params_differential.py'), ('set_creator', 'pump_set_creator_differential.py'), ('idl_authority', 'pump_idl_authority_differential.py'), ('legacy_create', 'pump_create_differential.py'), ('exact_quote_v3', 'pump_exact_quote_differential.py'), ('create_v2', 'pump_create_quote_differential.py'), ('legacy_sell', 'pump_legacy_sell_differential.py'), ('legacy_sell_configured_fee', 'pump_legacy_sell_configured_fee_differential.py'), ('sell_v2', 'pump_sell_v2_differential.py'), ('create_control', 'pump_create_control_differential.py'), ('migration', 'pump_migrate_differential.py'), ('v3_configured_fee', 'pump_v3_configured_fee_differential.py'), ('legacy_buy', 'pump_legacy_buy_differential.py'), ('buy_v2', 'pump_buy_v2_differential.py'), ('migrate_v2', 'pump_migrate_v2_differential.py'), ('cashback', 'pump_cashback_differential.py'), ('global_init', 'pump_global_init_differential.py'), ('holder_distribution', 'pump_holder_distribution_differential.py'), ('nested_create', 'pump_create_nested_differential.py'), ('quote_control', 'pump_quote_control_fresh_differential.py'), ('multi_hop_curve_partial', 'research/pump-multi-hop-corpus/harness.py')]
EXPECTED_CASES = {'volume': 66, 'administration': 93, 'creator_collection_v2': 154, 'extension': 308, 'exact_quote_v3': 352, 'sell_v2': 206, 'legacy_buy': 284, 'migrate_v2': 827, 'global_init': 40, 'buy': 334, 'creator_collection': 119, 'creator_distribution': 298, 'admin_cto': 363, 'set_params': 169, 'legacy_create': 87, 'migration': 228, 'holder_distribution': 649, 'multi_hop_curve_partial': 56, 'authority': 59, 'configuration': 351, 'sell': 301, 'minimum_distribution': 181, 'creator_migration': 139, 'set_creator': 509, 'legacy_sell': 115, 'legacy_sell_configured_fee': 28, 'v3_configured_fee': 372, 'cashback': 283, 'quote': 130, 'volume_sync': 341, 'fee_sweeps': 504, 'idl_authority': 171, 'create_v2': 297, 'create_control': 85, 'buy_v2': 216, 'nested_create': 48, 'quote_control': 507}

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
    assert result['inputs_unchanged']
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
    assert count == len(result['results'])
    assert all(row['matches'] and not row['different_fields'] for row in result['results'])
    return count


CASE_DIFFERENCE_FIELDS = ('different_fields', 'diff', 'differences', 'mismatched_fields')


def validate_case_results(result):
    """Reject explicit failed/incomplete pairs even if the summary says zero."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-directory', type=Path, default=ROOT / 'programs/pump')
    args = parser.parse_args()
    candidate = pin_program(args.candidate.resolve())
    original = ROOT / 'evidence/original/pump/deployed.so'
    runner = Path(__file__).resolve()
    candidate_sha, original_sha, runner_sha = map(sha, (candidate, original, runner))
    suites, scripts = {}, {}
    assert len(SUITES) == len(EXPECTED_CASES) == len({name for name, _ in SUITES}) == 44
    assert {name for name, _ in SUITES} == set(EXPECTED_CASES)
    retained = args.output.parent / (args.output.name + '.suites')
    suite_paths = [ROOT / filename if filename.startswith(('repro/', 'research/'))
                   else ROOT / 'scripts' / filename for _, filename in SUITES]
    source_paths = [path for path in args.source_directory.rglob('*')
                    if path.is_file() and 'target' not in path.relative_to(args.source_directory).parts
                    and (path.suffix == '.rs' or path.name in ('Cargo.toml', 'Cargo.lock'))]
    protect_inputs([args.output, *(retained / (name + '.json.gz') for name, _ in SUITES)],
                   [candidate, original, runner, ROOT / 'scripts/pump_diagnostic_audit.py',
                    *suite_paths, *source_paths])
    with tempfile.TemporaryDirectory(prefix='pump-differential-') as tmp:
        for name, filename in SUITES:
            script = ROOT / filename if filename.startswith(('repro/', 'research/')) else ROOT / 'scripts' / filename
            before = sha(script)
            output = Path(tmp) / (name + '.json')
            command = [sys.executable, str(script), '--candidate', str(candidate), '--output', str(output)]
            source_text = script.read_text()
            if "'--source-directory'" in source_text or '"--source-directory"' in source_text:
                command += ['--source-directory', str(args.source_directory.resolve())]
            subprocess.run(command, check=True, cwd=ROOT)
            assert before == sha(script), f'harness changed during execution: {filename}'
            assert runner_sha == sha(runner), 'aggregate runner changed during execution'
            assert candidate_sha == sha(candidate), 'candidate changed during execution'
            assert original_sha == sha(original), 'original changed during execution'
            raw = output.read_bytes()
            result = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
            if name == 'quote_control':
                count = validate_quote_control(result, candidate, original)
            elif name == 'multi_hop_curve_partial':
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
                validate_case_results(result)
            assert count == EXPECTED_CASES[name], (name, count, EXPECTED_CASES[name])
            assert not result.get('mismatches', result.get('failures', [])), name
            result['case_count'] = count
            suites[name] = result
            scripts[filename] = before
            retained.mkdir(parents=True, exist_ok=True)
            (retained / (name + '.json.gz')).write_bytes(
                gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
    assert sum(s['case_count'] for s in suites.values()) == 10468
    diagnostics = audit_diagnostics(suites)
    report = {
        'scope': 'Published 44-suite bounded Pump differential corpus. Per-suite limits remain in receipts; not full source recovery or binary identity.',
        'original_sha256': original_sha, 'candidate_sha256': candidate_sha,
        'runner_sha256': runner_sha, 'script_sha256': scripts,
        'case_count': sum(s['case_count'] for s in suites.values()),
        'source_directory': str(args.source_directory.resolve()),
        'diagnostic_audit_sha256': sha(ROOT / 'scripts/pump_diagnostic_audit.py'),
        'diagnostics': diagnostics,
        'mismatches': diagnostics['mismatches'], 'suites': suites,
    }
    raw = (json.dumps(report, separators=(',', ':')) + '\n').encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({'cases': report['case_count'], 'diagnostic_log_cases': diagnostics['log_bearing_cases'], 'mismatches': len(report['mismatches'])}))
    return bool(report['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
