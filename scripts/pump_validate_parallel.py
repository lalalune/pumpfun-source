#!/usr/bin/env python3
"""Build-bound parallel execution of the unchanged 44-suite main-Pump corpus."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_diagnostic_audit import audit
import pump_validate_all as base
sha = base.sha


def publish_report(path, payload):
    """Atomically replace a report, gzip-compressing only .gz destinations."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = gzip.compress(payload, mtime=0) if path.suffix == '.gz' else payload
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix='.' + path.name + '.',
                suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def validate_result(name, result, candidate, original):
    if name == 'quote_control':
        bound = result['bound_inputs_sha256']
        assert bound[str(candidate.relative_to(ROOT))] == sha(candidate)
        assert bound[str(original.relative_to(ROOT))] == sha(original)
        count = result['cases']
        assert count == len(result['results'])
        assert all(row['matches'] and not row['different_fields'] for row in result['results'])
    elif name == 'multi_hop_curve_partial':
        assert result['candidate_sha256'] == sha(candidate)
        assert result['original_pump_sha256'] == sha(original)
        assert result['passed'] == result['case_count'] == len(result['cases']) == 56
        assert all(not row['mismatches'] for row in result['cases'])
        count = result['case_count']
    elif name == 'tokenkeg_two_curve':
        count = base.validate_two_curve(result, sha(candidate), sha(original))
    else:
        assert result.get('original_sha256', result.get('provenance', {}).get(str(original))) == sha(original)
        assert result.get('candidate_sha256', result.get('provenance', {}).get(str(candidate))) == sha(candidate)
        count = base.retained_case_count(result)
    assert count == base.EXPECTED_CASES[name], (name, count, base.EXPECTED_CASES[name])
    assert not result.get('mismatches', result.get('failures', [])), name
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--source-directory', type=Path, required=True)
    parser.add_argument('--build-comparison', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--validate-existing', type=Path)
    parser.add_argument('--captured-loader', action='store_true')
    parser.add_argument('--shard', type=int, default=1)
    parser.add_argument('--shards', type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    assert 1 <= args.shard <= args.shards
    buckets = [[] for _ in range(args.shards)]
    loads = [0] * args.shards
    for entry in sorted(base.SUITES, key=lambda row: (-base.EXPECTED_CASES[row[0]], row[0])):
        slot = min(range(args.shards), key=lambda index: (loads[index], index))
        buckets[slot].append(entry)
        loads[slot] += base.EXPECTED_CASES[entry[0]]
    selected_suites = buckets[args.shard - 1]
    args.output = args.output.resolve()
    args.build_comparison = args.build_comparison.resolve()
    args.source_directory = args.source_directory.resolve()
    candidate = args.candidate.resolve()
    original = ROOT / 'evidence/original/pump/deployed.so'
    record = json.loads(args.build_comparison.read_text())
    assert record['returncode'] == 0 and record['source_unchanged']
    assert record['comparison']['candidate_sha256'] == sha(candidate)
    sources = record['source_sha256']
    assert all(sha(ROOT / k) == v for k, v in sources.items())
    bound_files = {str(p): sha(p) for p in [candidate, original, Path(__file__), Path(base.__file__), ROOT / 'scripts/pump_diagnostic_audit.py', args.build_comparison]}
    loader_wrapper = ROOT / 'scripts/pump_with_captured_loader.py'
    loader_inputs = [loader_wrapper, loader_wrapper.with_name('pump_captured_loader.py'), ROOT / 'evidence/original/pump/capture.json', ROOT / 'evidence/original/pump/program-account.bin', ROOT / 'evidence/original/pump/programdata-account.bin']
    if args.captured_loader:
        bound_files.update({str(p): sha(p) for p in loader_inputs})
    loader_receipts = {}
    scripts = {name: ROOT / filename if filename.startswith('repro/') else ROOT / 'scripts' / filename for name, filename in selected_suites}
    if record.get('portable_source_binding') and 'tokenkeg_two_curve' in scripts:
        scripts['tokenkeg_two_curve'] = ROOT / 'scripts/pump_tokenkeg_checkpoint_differential.py'
    script_hashes = {name: sha(path) for name, path in scripts.items()}
    suites, counts = {}, {}
    retained = args.output.parent / (args.output.name + '.suites')
    retained.mkdir(parents=True, exist_ok=True)

    def check_bound_files():
        assert all(sha(Path(p)) == digest for p, digest in bound_files.items())
        assert all(sha(ROOT / k) == v for k, v in sources.items())
        assert all(sha(scripts[name]) == digest for name, digest in script_hashes.items())

    def run_suite(name):
        script = scripts[name]
        with tempfile.TemporaryDirectory(prefix='pump-suite-' + name + '-') as tmp:
            output = Path(tmp) / 'result.json'
            command = [sys.executable, str(script), '--candidate', str(candidate), '--output', str(output)]
            loader_receipt = retained / (name + '.loader.json')
            if args.captured_loader:
                command = [sys.executable, str(loader_wrapper), '--receipt', str(loader_receipt), *command[1:]]
            source = script.read_text()
            if "'--source-directory'" in source or '"--source-directory"' in source:
                command += ['--source-directory', str(args.source_directory.resolve())]
            if name == 'tokenkeg_two_curve':
                command += ['--build-report', str(args.build_comparison)]
                if '--source-directory' not in command:
                    command += ['--source-directory', str(args.source_directory.resolve())]
            completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            (retained / (name + '.log')).write_text(completed.stdout)
            completed.check_returncode()
            raw = output.read_bytes()
            result = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        (retained / (name + '.json.gz')).write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        count = validate_result(name, result, candidate, original)
        if args.captured_loader:
            loaded = json.loads(loader_receipt.read_text())
            assert loaded['loads'], name
            expected = {sha(candidate), sha(original)}
            assert {row['elf_sha256'] for row in loaded['loads']} == expected, name
            assert all(row['program_bytes'] == 36 and row['program_owner'] == 'BPFLoaderUpgradeab1e11111111111111111111111' and row['programdata_bytes'] == 10485760 and row['elf_prefix_unchanged'] and row['zero_allocation_tail'] for row in loaded['loads']), name
            assert all(sha(Path(path)) == digest for path, digest in loaded['input_sha256'].items())
            loader_receipts[name] = {'path': str(loader_receipt.relative_to(ROOT)), 'sha256': sha(loader_receipt), 'load_count': len(loaded['loads'])}
        check_bound_files()
        result['case_count'] = count
        (retained / (name + '.json.gz')).write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        return name, count, result

    if args.validate_existing:
        raw = args.validate_existing.read_bytes()
        previous = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        assert set(previous['suites']) == set(scripts)
        assert previous.get('loader_profile', 'legacy-raw') == ('captured-upgradeable' if args.captured_loader else 'legacy-raw')
        expected_previous_scripts = {str(scripts[name].relative_to(ROOT)): script_hashes[name]
                                     for name, _ in selected_suites}
        assert previous['script_sha256'] == expected_previous_scripts, 'saved report harness hashes differ'
        assert previous['compiled_source_sha256'] == sources, 'saved report compiled-source binding differs'
        bound_files[str(args.validate_existing.resolve())] = sha(args.validate_existing)
        for name, result in previous['suites'].items():
            counts[name] = validate_result(name, result, candidate, original)
            suites[name] = result
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            jobs = {executor.submit(run_suite, name): name for name, _ in selected_suites}
            errors = []
            for future in as_completed(jobs):
                if future.cancelled():
                    continue
                try:
                    name, count, result = future.result()
                except Exception as exc:
                    errors.append({'suite': jobs[future], 'error': repr(exc), 'traceback': traceback.format_exc()})
                    print(json.dumps({'failed': jobs[future], 'error': repr(exc)}), flush=True)
                    for pending in jobs:
                        pending.cancel()
                    continue
                suites[name], counts[name] = result, count
                print(json.dumps({'completed': name, 'cases': count, 'suite_count': len(suites)}), flush=True)
            if errors:
                failure = {
                    'complete': False,
                    'candidate_sha256': sha(candidate),
                    'completed_suites': list(suites),
                    'errors': errors,
                    'bound_files_sha256': bound_files,
                }
                publish_report(
                    args.output.with_name(args.output.name + '.failed.json'),
                    (json.dumps(failure, indent=2) + '\n').encode())
                raise RuntimeError('suite failure; completed receipts and logs retained')
    check_bound_files()
    assert len(suites) == len(selected_suites) and sum(counts.values()) == loads[args.shard - 1]
    assert set(suites) == {name for name, _ in selected_suites}
    diagnostics = audit(suites)
    report = {'scope': __doc__ + ' Per-suite limits still apply; no whole-ELF identity claim.',
              'candidate_sha256': sha(candidate), 'original_sha256': sha(original),
              'bound_files_sha256': bound_files, 'compiled_source_sha256': sources,
              'source_directory': str(args.source_directory.resolve()),
              'script_sha256': {str(scripts[name].relative_to(ROOT)): digest for name, digest in script_hashes.items()},
              'workers': 0 if args.validate_existing else args.workers,
              'shard': args.shard, 'shards': args.shards, 'suite_schedule': [name for name, _ in selected_suites],
              'loader_profile': 'captured-upgradeable' if args.captured_loader else 'legacy-raw',
              'loader_receipts': loader_receipts,
              'validation_only_source_sha256': sha(args.validate_existing) if args.validate_existing else None,
              'case_count': sum(counts.values()), 'diagnostics': diagnostics,
              'mismatches': diagnostics['mismatches'], 'suites': suites}
    publish_report(
        args.output,
        json.dumps(report, separators=(',', ':')).encode())
    print(json.dumps({'case_count': report['case_count'], 'suites': len(suites), 'diagnostic_log_cases': diagnostics['log_bearing_cases'], 'diagnostic_mismatches': len(diagnostics['mismatches'])}))
    return bool(diagnostics['mismatches'])


if __name__ == '__main__':
    raise SystemExit(main())
