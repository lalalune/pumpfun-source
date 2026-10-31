#!/usr/bin/env python3
"""Replay the frozen two-curve Pump fixture with a current, exact source manifest.

Only build binding changes: VM execution and fixtures use the original harness.
The captured caller dependency is unchanged; this tests the main Pump contract.
"""
if not __debug__:
    raise RuntimeError('Two-curve replay requires normal Python; do not use -O or PYTHONOPTIMIZE')

import argparse
import gzip
import importlib.util
import json
import tomllib
from pathlib import Path
from pump_differential_output import PumpReport

from build_source_manifest import source_manifest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = ROOT / 'programs/pump'
HISTORICAL = ROOT / 'research/pump-two-curve-inputs/fixture/pump_tokenkeg_two_curve_differential.py'
spec = importlib.util.spec_from_file_location('pump_two_curve_frozen', HISTORICAL)
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def compiled_binding(candidate, build_report):
    assert build_report is not None, 'Candidate requires its actual build report'
    report = json.loads(build_report.read_text())
    attempt_path = build_report.with_name('build-attempt.json')
    attempt = json.loads(attempt_path.read_text())
    assert attempt['returncode'] == 0 and attempt['source_unchanged']
    assert attempt['source_sha256'] == attempt['source_after_sha256'] == report['source_sha256']
    # Preserve the actual workspace manifest and lockfile in the build binding.
    manifest = SOURCE_DIRECTORY / 'Cargo.toml'
    package = tomllib.loads(manifest.read_text())
    workspace = SOURCE_DIRECTORY
    if 'workspace' not in package:
        for parent in SOURCE_DIRECTORY.parents:
            parent_manifest = parent / 'Cargo.toml'
            if parent_manifest.is_file() and 'workspace' in tomllib.loads(parent_manifest.read_text()):
                workspace = parent
                break
            if parent == ROOT:
                break
    assert report['source_sha256'] == source_manifest(SOURCE_DIRECTORY, workspace, ROOT, cwd=workspace)
    assert report['comparison']['candidate_sha256'] == fixture.sha(candidate)
    # Aggregate runners admit an explicit receipt from outside the checkout.
    label = build_report.relative_to(ROOT) if build_report.is_relative_to(ROOT) else build_report
    return {'report': str(label),
            'report_sha256': fixture.sha(build_report),
            'attempt_sha256': fixture.sha(attempt_path),
            'candidate_sha256': fixture.sha(candidate),
            'actual_source_sha256': report['source_sha256']}


fixture.compiled_binding = compiled_binding


def bindings(candidate, report):
    result = fixture.bindings(candidate, report)
    for path in (Path(__file__).resolve(), ROOT / 'scripts/build_source_manifest.py'):
        result['repository_inputs'][str(path.relative_to(ROOT))] = fixture.sha(path)
    return result


def main():
    global SOURCE_DIRECTORY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--build-report', type=Path)
    parser.add_argument('--source-directory', type=Path, default=ROOT / 'programs/pump')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    SOURCE_DIRECTORY = args.source_directory.resolve()
    candidate = args.candidate.resolve()
    report = (args.build_report or candidate.parent / 'build-comparison.json').resolve()
    output = PumpReport(args.output, ROOT, candidate, __file__,
                        extra_inputs=(report, report.with_name('build-attempt.json'), SOURCE_DIRECTORY),
                        overwrite=False)
    before = bindings(candidate, report)
    rows = []
    for name, sell, amount, mode, limit in fixture.fixtures():
        original = fixture.invoke(sell, amount, mode, limit)
        current = fixture.invoke(sell, amount, mode, limit, candidate)
        fields = ('error', 'events', 'inner', 'return_data', 'before', 'after', 'pump_calls', 'token_calls')
        rows.append({'case': name, 'parameters': {'sell': sell, 'amount': amount, 'fee_mode': mode, 'limit': limit},
                     'original': original, 'candidate': current,
                     'mismatches': [key for key in fields if original[key] != current[key]]})
    assert before == bindings(candidate, report)
    result = {'scope': __doc__, 'provenance': before, 'inputs_unchanged': True,
              'candidate_sha256': fixture.sha(candidate), 'case_count': len(rows),
              'original_successes': sum(row['original']['error'] is None for row in rows),
              'original_pump_cpi_cases': sum(bool(row['original']['pump_calls']) for row in rows),
              'verified_outer_signatures': sum(row[side]['verified_signature_count'] for row in rows for side in ('original', 'candidate')),
              'cases': rows}
    raw = json.dumps(result, separators=(',', ':')).encode()
    output.write(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({key: result[key] for key in ('case_count', 'original_successes', 'original_pump_cpi_cases', 'verified_outer_signatures')}))
    assert all(not row['mismatches'] for row in rows)


if __name__ == '__main__':
    main()
