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
from pump_amm_reusable_harness import pin_program
sha = base.sha
protect_inputs = base.protect_inputs


def report_destinations(output, suites, captured_loader, execute):
    """List every file this invocation can publish, including failure sidecars."""
    paths = [output]
    if execute:
        paths.append(output.with_name(output.name + '.failed.json'))
        retained = output.parent / (output.name + '.suites')
        for name in suites:
            paths.extend(retained / (name + suffix) for suffix in ('.log', '.json.gz'))
            if captured_loader:
                paths.append(retained / (name + '.loader.json'))
    return paths


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
        count = base.validate_quote_control(result, candidate, original)
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
        base.validate_case_results(result)
    assert count == base.EXPECTED_CASES[name], (name, count, base.EXPECTED_CASES[name])
    assert not result.get('mismatches', result.get('failures', [])), name
    return count


def validate_loader_receipt(name, path, script, candidate, original, inputs):
    """Admit the actual retained loader evidence for execution and revalidation."""
    loaded = json.loads(path.read_text())
    assert loaded['loads'], name
    assert Path(loaded['harness']).resolve() == script.resolve(), name
    expected_inputs = {str(p): sha(p) for p in [*inputs, script]}
    assert loaded['input_sha256'] == expected_inputs, (name, 'loader inputs differ')
    assert {row['elf_sha256'] for row in loaded['loads']} == {sha(candidate), sha(original)}, name
    assert all(row['program_bytes'] == 36 and row['program_owner'] == 'BPFLoaderUpgradeab1e11111111111111111111111' and row['programdata_bytes'] == 10485760 and row['elf_prefix_unchanged'] and row['zero_allocation_tail'] for row in loaded['loads']), name
    return {'path': base.bound_input_key(path, ROOT), 'sha256': sha(path),
            'load_count': len(loaded['loads'])}


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
    candidate = pin_program(args.candidate.resolve())
    original = ROOT / 'evidence/original/pump/deployed.so'
    record = json.loads(args.build_comparison.read_text())
    assert record['returncode'] == 0 and record['source_unchanged']
    assert record['comparison']['candidate_sha256'] == sha(candidate)
    sources = record['source_sha256']
    assert all(sha(ROOT / k) == v for k, v in sources.items())
    bound_files = {str(p): sha(p) for p in [candidate, original, Path(__file__), Path(base.__file__), ROOT / 'scripts/pump_diagnostic_audit.py', args.build_comparison]}
    loader_wrapper = ROOT / 'scripts/pump_with_captured_loader.py'
    loader_inputs = [loader_wrapper, loader_wrapper.with_name('pump_captured_loader.py'), ROOT / 'evidence/original/pump/capture.json', ROOT / 'evidence/original/pump/program-account.bin', ROOT / 'evidence/original/pump/programdata-account.bin', original]
    if args.captured_loader:
        bound_files.update({str(p): sha(p) for p in loader_inputs})
    loader_receipts = {}
    scripts = {name: ROOT / filename if filename.startswith(('repro/', 'research/')) else ROOT / 'scripts' / filename for name, filename in selected_suites}
    if record.get('portable_source_binding') and 'tokenkeg_two_curve' in scripts:
        scripts['tokenkeg_two_curve'] = ROOT / 'scripts/pump_tokenkeg_checkpoint_differential.py'
    script_hashes = {name: sha(path) for name, path in scripts.items()}
    suites, counts = {}, {}
    failed_suite_outputs = {}
    retained = args.output.parent / (args.output.name + '.suites')
    previous = None
    protected = [*bound_files, *(ROOT / name for name in sources), *scripts.values()]
    if args.validate_existing:
        raw = args.validate_existing.read_bytes()
        previous = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        bound_files[str(args.validate_existing.resolve())] = sha(args.validate_existing)
        protected.append(args.validate_existing)
        if args.captured_loader:
            protected.extend(ROOT / row['path'] for row in previous['loader_receipts'].values())
    protect_inputs(report_destinations(args.output, scripts, args.captured_loader,
                                      not args.validate_existing), protected)
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
            if completed.returncode and output.is_file():
                raw = output.read_bytes()
                rejected = retained / (name + '.failed-output')
                rejected.write_bytes(raw)
                failed_suite_outputs[name] = {
                    'path': base.bound_input_key(rejected, ROOT),
                    'sha256': sha(rejected), 'bytes': len(raw),
                    'returncode': completed.returncode,
                }
            completed.check_returncode()
            raw = output.read_bytes()
            result = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
        (retained / (name + '.json.gz')).write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        count = validate_result(name, result, candidate, original)
        if args.captured_loader:
            loader_receipts[name] = validate_loader_receipt(name, loader_receipt, script, candidate, original, loader_inputs)
        check_bound_files()
        result['case_count'] = count
        (retained / (name + '.json.gz')).write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        return name, count, result

    if args.validate_existing:
        assert set(previous['suites']) == set(scripts)
        assert previous.get('loader_profile', 'legacy-raw') == ('captured-upgradeable' if args.captured_loader else 'legacy-raw')
        expected_previous_scripts = {str(scripts[name].relative_to(ROOT)): script_hashes[name]
                                     for name, _ in selected_suites}
        assert previous['script_sha256'] == expected_previous_scripts, 'saved report harness hashes differ'
        assert previous['compiled_source_sha256'] == sources, 'saved report compiled-source binding differs'
        if args.captured_loader:
            assert set(previous['loader_receipts']) == set(scripts), 'saved loader evidence is incomplete'
            for name, saved in previous['loader_receipts'].items():
                receipt = (ROOT / saved['path']).resolve()
                assert sha(receipt) == saved['sha256'], (name, 'saved loader receipt changed')
                entry = validate_loader_receipt(name, receipt, scripts[name], candidate, original, loader_inputs)
                assert entry == saved, (name, 'saved loader receipt binding differs')
                loader_receipts[name] = entry
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
                    'failed_suite_outputs': failed_suite_outputs,
                    'bound_files_sha256': bound_files,
                }
                publish_report(
                    args.output.with_name(args.output.name + '.failed.json'),
                    (json.dumps(failure, indent=2) + '\n').encode())
                raise RuntimeError('suite failure; completed receipts and logs retained')
    for entry in loader_receipts.values():
        bound_files[str((ROOT / entry['path']).resolve())] = entry['sha256']
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
