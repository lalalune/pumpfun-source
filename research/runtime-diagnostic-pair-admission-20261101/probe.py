"""Replay authentic retained logs through the diagnostic-audit CLI; no VM runs."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

RECEIPT = 'research/handler-closure-multihop-mayhem-20261029/receipts/multi_hop_three_curve_cu14.json.gz'
RECEIPT_SHA256 = '1b9212cf8107193430d77f1f48773f172ff94c77fe4cbad985945201ea338a8c'
SCRIPT = 'scripts/pump_diagnostic_audit.py'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def scenarios(document):
    yield 'intact', copy.deepcopy(document), 'complete'
    mismatched = copy.deepcopy(document)
    # Retain both genuine diagnostic payloads. This is a consumer-only splice,
    # not a claim that these two different transactions are a runtime pair.
    mismatched['cases'][8]['candidate'] = copy.deepcopy(document['cases'][9]['candidate'])
    yield 'authentic_other_outcome', mismatched, 'mismatch'
    for side in ('original', 'candidate'):
        for kind in ('absent', 'null', 'scalar', 'list'):
            changed = copy.deepcopy(mismatched)
            if kind == 'absent':
                del changed['cases'][8][side]
            else:
                changed['cases'][8][side] = {'null': None, 'scalar': 'outcome lost', 'list': []}[kind]
            yield side + '_' + kind, changed, ('optional_outcome' if kind in ('absent', 'null')
                                               else 'malformed_outcome')
        changed = copy.deepcopy(mismatched)
        del changed['cases'][8][side]['logs']
        yield side + '_missing_logs', changed, 'incomplete_logs'
    for empty in (False, True):
        changed = copy.deepcopy(mismatched)
        for side in ('original', 'candidate'):
            if empty:
                changed['cases'][8][side]['logs'] = []
            else:
                del changed['cases'][8][side]['logs']
        yield ('empty' if empty else 'absent') + '_both_logs', changed, 'optional_logs'
    changed = copy.deepcopy(document)
    # Non-execution metadata may use these names without supplying log sources.
    changed['source_notes'] = {'original': {'description': 'retained input'}, 'candidate': None}
    changed['names'] = {'original': 'original', 'candidate': 'candidate'}
    yield 'unrelated_metadata', changed, 'complete'
    changed = copy.deepcopy(document)
    changed['calibration'] = [{'case': row['case'], 'original': copy.deepcopy(row['original'])}
                              for row in document['cases'][8:10]]
    yield 'original_only_calibration', changed, 'complete'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', help='Run the exact audit script at this Git revision')
    parser.add_argument('--optimize', action='store_true')
    args = parser.parse_args()
    repo = args.repo.resolve()
    raw = (repo / RECEIPT).read_bytes()
    if sha(raw) != RECEIPT_SHA256:
        raise ValueError('retained receipt hash differs')
    document = json.loads(gzip.decompress(raw))
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    with tempfile.TemporaryDirectory(prefix='diagnostic-script-') as temporary:
        script = repo / SCRIPT
        if args.revision:
            script = Path(temporary) / 'pump_diagnostic_audit.py'
            script.write_bytes(subprocess.check_output(['git', 'show', args.revision + ':' + SCRIPT], cwd=repo))
        script_hash = sha(script.read_bytes())
        for label, data, kind in scenarios(document):
            for compressed in (False, True):
                name = label + ('-gzip' if compressed else '-plain')
                source = args.output / (name + '.input')
                output = args.output / (name + '.audit.json')
                encoded = (json.dumps({'suites': {'retained': data}}) + '\n').encode()
                if compressed:
                    encoded = gzip.compress(encoded, mtime=0)
                source.write_bytes(encoded)
                command = [sys.executable, *(['-O'] if args.optimize else []), '-B', str(script),
                           '--report', str(source), '--output', str(output)]
                completed = subprocess.run(command, cwd=repo, text=True, capture_output=True, timeout=30)
                (args.output / (name + '.log')).write_text(completed.stdout + completed.stderr, encoding='utf-8')
                report = json.loads(output.read_bytes()) if output.exists() else None
                diagnostics = ({key: report[key] for key in ('coverage', 'log_bearing_cases', 'mismatches')}
                               if report else None)
                rows.append({'scenario': label, 'kind': kind, 'gzip_input': compressed,
                             'returncode': completed.returncode, 'published': output.exists(),
                             'log_bearing_cases': report['log_bearing_cases'] if report else None,
                             'mismatches': len(report['mismatches']) if report else None,
                             'diagnostics_sha256': sha(json.dumps(diagnostics, sort_keys=True).encode()) if report else None,
                             'input_unchanged': source.read_bytes() == encoded,
                             'staging_files': [path.name for path in args.output.glob('.' + output.name[:32] + '.*')],
                             'rejection_names_missing_side': 'execution pair is missing' in completed.stderr,
                             'rejection_names_malformed_side': 'execution pair has malformed' in completed.stderr})
        if sha(script.read_bytes()) != script_hash:
            raise ValueError('audit script changed during replay')
    summary = {'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
               'script_revision': args.revision or 'working-tree', 'script_sha256': script_hash,
               'source': RECEIPT, 'source_sha256': RECEIPT_SHA256,
               'source_unchanged': (repo / RECEIPT).read_bytes() == raw,
               'retained_cases': len(document['cases']), 'optimized_children': args.optimize,
               'new_vm_executions': 0, 'results': rows,
               'limits': 'Actual audit CLI over owned copies of an authentic retained receipt. The other-outcome splice is a consumer negative control, not new paired runtime evidence. Cases lacking both log sources remain outside the optional diagnostic audit.'}
    (args.output / 'results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
