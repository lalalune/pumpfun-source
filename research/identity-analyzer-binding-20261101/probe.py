"""Exercise the reviewed audit wrapper on all nine retained ELF captures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

WRAPPER = Path('reconstruction/diagnostics/identity-audit-unoptimized/run.py')
SOURCES = tuple(Path('scripts') / name for name in
                ('reconstruction_identity_audit.py', 'analyze.py', 'compare.py'))
MODES = (((), None), (('-O',), None), (('-OO',), None), ((), '1'), ((), '2'))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reproduce(repo, revision=None):
    repo = Path(repo).resolve()
    sources = {path: (repo / path).read_bytes() for path in SOURCES}
    wrapper = (subprocess.check_output(['git', '-C', str(repo), 'show',
                                       f'{revision}:{WRAPPER.as_posix()}'])
               if revision else (repo / WRAPPER).read_bytes())
    captures = {path.relative_to(repo): path.read_bytes()
                for path in sorted((repo / 'evidence').glob('*/*/deployed.so'))}
    if len(captures) != 9:
        raise ValueError('expected all nine retained captures')
    result = {'wrapper_sha256': sha(wrapper),
              'source_sha256': {str(p): sha(raw) for p, raw in sources.items()},
              'capture_sha256': {str(p): sha(raw) for p, raw in captures.items()},
              'rows': [], 'controls': []}
    with tempfile.TemporaryDirectory(prefix='identity-binding-proof-') as temporary:
        root = Path(temporary)
        # Keep the wrapper at its repository depth: it resolves its default
        # ROOT as parents[3], which a shallow temporary file (/tmp/x/wrapper.py)
        # does not have.
        runner = root / WRAPPER
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_bytes(wrapper)
        for path, raw in captures.items():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        index = {'programs': {str(path.parent): {
            'original_path': str(path), 'candidate_path': str(path),
            'original_sha256': sha(raw), 'candidate_sha256': sha(raw),
        } for path, raw in captures.items()}}
        (root / 'index.json').write_text(json.dumps(index), encoding='utf-8')

        def invoke(script, label, flags=(), optimize=None, index_name='index.json', output=None):
            destination = output or root / (label + '.json')
            environment = dict(os.environ)
            environment.pop('PYTHONOPTIMIZE', None)
            if optimize is not None:
                environment['PYTHONOPTIMIZE'] = optimize
            run = subprocess.run([sys.executable, '-B', *flags, str(script),
                                  '--repo', str(root), '--index', index_name,
                                  '--output', str(destination)], env=environment,
                                 cwd=root, capture_output=True, text=True)
            return run, destination

        for ending in ('LF', 'CRLF'):
            for path, raw in sources.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                normalized = raw.replace(b'\r\n', b'\n')
                target.write_bytes(normalized if ending == 'LF' else normalized.replace(b'\n', b'\r\n'))
            direct, output = invoke(root / SOURCES[0], ending + '-direct')
            if direct.returncode:
                raise ValueError(direct.stderr)
            baseline = output.read_bytes()
            decoded = json.loads(baseline)
            if len(decoded['snapshot_programs']) != 9:
                raise ValueError('incomplete direct audit')
            if any(not row['allocation_comparison']['full_byte_equality'] or
                   row['source_completeness_inferred'] or row['historical_compiler_identity_proven']
                   for row in decoded['snapshot_programs'].values()):
                raise ValueError('invalid identical-capture control')
            for number, (flags, optimize) in enumerate(MODES):
                run, output = invoke(runner, f'{ending}-{number}', flags, optimize)
                payload = output.read_bytes() if output.exists() else None
                result['rows'].append({'line_endings': ending, 'flags': list(flags),
                    'environment_optimize': optimize, 'exit': run.returncode,
                    'report_sha256': sha(payload) if payload is not None else None,
                    'direct_report_sha256': sha(baseline),
                    'matches_direct': payload == baseline,
                    'reviewed_source_refusal': 'reviewed identity audit source changed: scripts/analyze.py' in run.stderr})
            for number, path in enumerate(SOURCES):
                target = root / path
                original = target.read_bytes()
                target.write_bytes(original + b'\n# unreviewed edit\n')
                run, output = invoke(runner, f'{ending}-changed-{number}')
                result['controls'].append({'case': 'changed-source', 'line_endings': ending,
                    'path': str(path), 'rejected': run.returncode != 0 and not output.exists()
                    and 'reviewed identity audit source changed' in run.stderr})
                target.write_bytes(original)
            prior = root / (ending + '-prior.json')
            prior.write_bytes(b'previous audit\n')
            run, _ = invoke(runner, 'occupied', output=prior)
            result['controls'].append({'case': 'occupied-report', 'line_endings': ending,
                'rejected': run.returncode != 0 and prior.read_bytes() == b'previous audit\n'})
            for field in ('original_sha256', 'candidate_sha256'):
                wrong = json.loads(json.dumps(index))
                next(iter(wrong['programs'].values()))[field] = '0' * 64
                (root / 'wrong.json').write_text(json.dumps(wrong), encoding='utf-8')
                run, output = invoke(runner, f'{ending}-wrong-{field}', ('-O',), '2', 'wrong.json')
                result['controls'].append({'case': field, 'line_endings': ending,
                    'rejected': run.returncode != 0 and not output.exists(),
                    'reached_digest_check': field.split('_')[0] + ' SHA-256 mismatch' in run.stderr})
        result['temporary_inputs_preserved'] = all((root / p).read_bytes() == raw for p, raw in captures.items())
    result['repository_inputs_preserved'] = all((repo / p).read_bytes() == raw
                                               for p, raw in {**sources, **captures}.items())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--revision', help='read the wrapper from this exact local Git revision')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error('choose a fresh proof output')
    report = reproduce(args.repo, args.revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'runs': len(report['rows']),
                      'successful': sum(row['exit'] == 0 for row in report['rows']),
                      'controls': len(report['controls'])}))


if __name__ == '__main__':
    main()
