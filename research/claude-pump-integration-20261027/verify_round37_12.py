#!/usr/bin/env python3
"""Replay the two Round37-12 recipes and their four captured-loader reports."""
import gzip
import hashlib
import importlib.util
import json
import tarfile
from pathlib import Path
import subprocess
import sys

if not __debug__:
    raise RuntimeError('Evidence verification requires ordinary Python')
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'evidence/original/pump/deployed.so').is_file())
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_diagnostic_audit import audit
from pump_validate_all import EXPECTED_CASES
from pump_compare_function_bytes import normalize, body
from pump_quote_control_function_match import sections


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data)


def check_report(report, candidate_hash, original_hash):
    assert report['candidate_sha256'] == candidate_hash, 'wrong regression candidate'
    assert report['original_sha256'] == original_hash
    for name, digest in report['script_sha256'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == digest, 'regression harness changed'
    assert report['loader_profile'] == 'captured-upgradeable'
    assert not report['mismatches']
    assert set(report['suites']) == set(EXPECTED_CASES), 'missing regression suite'
    assert report['case_count'] == sum(EXPECTED_CASES.values()) == 10468
    assert report['diagnostics']['log_bearing_cases'] == 10464
    for name, result in report['suites'].items():
        assert result['case_count'] == EXPECTED_CASES[name], name
        assert not result.get('mismatches', result.get('failures', [])), name
        if name != 'quote_control':
            assert len(result['cases']) == EXPECTED_CASES[name], name
        if name == 'quote_control':
            values = result['bound_inputs_sha256'].values()
            assert candidate_hash in values and original_hash in values
            assert all(row['matches'] and not row['different_fields'] for row in result['results'])
        elif name == 'tokenkeg_two_curve':
            assert result['candidate_sha256'] == candidate_hash
            assert result['provenance']['repository_inputs']['evidence/original/pump/deployed.so'] == original_hash
            assert result['inputs_unchanged'] and result['verified_outer_signatures'] == 40
            assert all(row['candidate'] is not None and not row['mismatches'] for row in result['cases'])
        elif name == 'multi_hop_curve_partial':
            assert result['candidate_sha256'] == candidate_hash
            assert result['original_pump_sha256'] == original_hash
            assert result['passed'] == len(result['cases']) == 56
            assert all(not row['mismatches'] for row in result['cases'])
        else:
            assert result.get('candidate_sha256') == candidate_hash or candidate_hash in result.get('provenance', {}).values(), name
            assert result.get('original_sha256') == original_hash or original_hash in result.get('provenance', {}).values(), name
    diagnostics = audit(report['suites'])
    assert not diagnostics['mismatches'] and diagnostics['log_bearing_cases'] == 10464


def check_loaders(report, archive, candidate_hash, original_hash):
    receipts = report['loader_receipts']
    assert set(receipts) == set(EXPECTED_CASES)
    program_hash = sha(ROOT / 'evidence/original/pump/program-account.bin')
    data = (ROOT / 'evidence/original/pump/programdata-account.bin').read_bytes()
    header_hash = hashlib.sha256(data[:45]).hexdigest()
    with tarfile.open(archive, 'r:gz') as bundle:
        assert set(bundle.getnames()) == {name + '.loader.json' for name in receipts}
        for name, metadata in receipts.items():
            raw = bundle.extractfile(name + '.loader.json').read()
            assert hashlib.sha256(raw).hexdigest() == metadata['sha256']
            loaded = json.loads(raw)
            assert len(loaded['loads']) == metadata['load_count'] > 0
            assert {row['elf_sha256'] for row in loaded['loads']} == {candidate_hash, original_hash}
            for row in loaded['loads']:
                assert row['program_bytes'] == 36 and row['programdata_bytes'] == 10485760
                assert row['program_owner'] == 'BPFLoaderUpgradeab1e11111111111111111111111'
                assert row['program_sha256'] == program_hash and row['header_sha256'] == header_hash
                assert row['elf_prefix_unchanged'] and row['zero_allocation_tail']


def staged_hashes(crate):
    text = (crate / 'Cargo.toml').read_text()
    profile, workspace = text.index('[profile.release]'), text.index('[workspace]')
    expected = {'programs/pump/' + str(p.relative_to(crate)): sha(p)
                for p in crate.rglob('*') if p.is_file() and p.name not in ('Cargo.toml', 'Cargo.lock')}
    expected['programs/pump/Cargo.toml'] = hashlib.sha256((text[:profile].rstrip() + '\n').encode()).hexdigest()
    expected['Cargo.toml'] = hashlib.sha256(('[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + text[profile:workspace].strip() + '\n').encode()).hexdigest()
    expected['Cargo.lock'] = sha(crate / 'Cargo.lock')
    return expected


def main():
    original = ROOT / 'evidence/original/pump/deployed.so'
    original_hash = sha(original)
    spec = importlib.util.spec_from_file_location('round37_package_reader', HERE / 'r37-genuine-12/verify.py')
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    summary = {}
    for kind, identity_count, repository_count in [('genuine', 813, 808), ('layout', 907, 902)]:
        package = HERE / f'r37-{kind}-12'
        process = subprocess.run([sys.executable, '-I', '-B', str(package / 'verify.py')], capture_output=True, text=True)
        assert process.returncode == 0, process.stdout + process.stderr
        result = read(package / 'RESULT.json')
        assert result['counts']['normalized'] == repository_count and result['counts']['raw'] == 147
        assert not result['normalized_losses'] and not result['raw_losses']
        assert result['regression']['mismatches'] == 0
        package_report = read(package / 'full.json.gz')
        check_report(package_report, sha(package / 'candidate.so'), original_hash)
        check_loaders(package_report, package / 'loader-receipts.tar.gz', sha(package / 'candidate.so'), original_hash)
        snapshot = HERE / 'wip-20261028' / f'integ-{kind}-r37-12'
        assert reader.tree_files(snapshot / 'src') == reader.tree_files(package / 'source/programs/pump'), 'recipe source trees differ'
        proof = HERE / 'round37-12-validation' / ('identity-' + kind)
        manifest = read(proof / 'MANIFEST.json')
        actual = {str(p.relative_to(proof)) for p in proof.rglob('*') if p.is_file()}
        assert actual == set(manifest) | {'MANIFEST.json'}
        assert all(sha(proof / name) == digest for name, digest in manifest.items())
        rebuilt = read(proof / 'RESULT.json')
        assert rebuilt['ok'] and rebuilt['runtime_valid'] and not rebuilt['stack_warnings']
        assert rebuilt['matches_snapshot_unstripped'] and rebuilt['matches_snapshot_candidate']
        assert rebuilt['unstripped_sha256'] == sha(snapshot / 'unstripped.so')
        assert rebuilt['candidate_sha256'] == sha(snapshot / 'candidate.so')
        record = read(proof / 'build-comparison.json')
        assert record['builder_sha256'] == sha(HERE / 'wip-20261028/harness/fastbuild.py')
        assert record['returncode'] == 0 and record['source_unchanged'] and record['recipe'] == 'identity'
        prefix = f'work/pr401-review/identity-{kind}/source/'
        bound = record['source_sha256']
        assert all(name.startswith(prefix) for name in bound)
        assert {name[len(prefix):]: digest for name, digest in bound.items()} == staged_hashes(snapshot / 'src')
        report = read(proof / 'full.json.gz')
        assert report['compiled_source_sha256'] == bound
        check_report(report, sha(snapshot / 'candidate.so'), original_hash)
        check_loaders(report, proof / 'loader-receipts.tar.gz', sha(snapshot / 'candidate.so'), original_hash)
        # Recompute the snapshot inventory independently from the submitted score.
        import csv
        elf = (snapshot / 'unstripped.so').read_bytes()
        secs = sections(elf)
        by = {}
        for start, size, _ in reader.elf_functions(elf):
            raw = body(elf, secs, start, size)
            normalized, _ = normalize(raw, start, secs)
            by.setdefault((size, hashlib.sha256(normalized).hexdigest()), []).append(hashlib.sha256(raw).hexdigest())
        orig = original.read_bytes(); original_sections = sections(orig)
        normalized_count = raw_count = 0
        with (ROOT / 'repro/reconstruction-status-2026-10-26/functions.tsv').open() as handle:
            for row in csv.DictReader(handle, delimiter='\t'):
                if row['program'] != 'pump' or row['variant'] != 'selected':
                    continue
                start, end = int(row['original_start']), int(row['original_end'])
                raw = body(orig, original_sections, start, end - start)
                normalized, _ = normalize(raw, start, original_sections)
                matches = by.get((end - start, hashlib.sha256(normalized).hexdigest()), [])
                normalized_count += bool(matches)
                raw_count += hashlib.sha256(raw).hexdigest() in matches
        assert (normalized_count, raw_count) == (identity_count, 165)
        summary[kind] = {'identity_normalized': identity_count, 'repository_normalized': repository_count, 'cases_per_recipe': 10468}
    print(json.dumps({'verified': True, 'recipes': summary, 'whole_elf_equal': False}, indent=2))


if __name__ == '__main__':
    main()
