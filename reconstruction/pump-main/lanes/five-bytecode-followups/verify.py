#!/usr/bin/env python3
"""Rescore supplied ELF builds against this source-bound measurement packet."""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT,
                        help='Checkout containing the recorded source and exact scoring inputs')
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    root = args.repo.resolve()
    sys.path.insert(0, str(root / 'reconstruction/harness'))
    import score
    from source_inputs import snapshot
    require(not args.report.exists(), 'report already exists')
    manifest = json.loads((HERE / 'MEASUREMENTS.json').read_text())
    for relative, expected_hash in manifest['inputs'].items():
        path = root / relative
        require(path.resolve().is_relative_to(root), 'input escapes repository')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash,
                'recorded input differs: ' + relative)
    before = {name: hashlib.sha256(path.read_bytes()).hexdigest()
              for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]}
    source = snapshot(root / 'programs/pump')
    require(source == json.loads((HERE / 'candidate-source.json').read_text()),
            'current program source does not match the recorded candidate')
    results = {}
    for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]:
        require(before[name] == manifest[name]['unstripped_sha256'], name + ' ELF hash mismatch')
        expected = json.loads(gzip.decompress((HERE / (name + '-score.json.gz')).read_bytes()))
        actual = score.score(path)
        actual = {str(k): v for k, v in actual.items()}
        require(actual == expected['windows'], name + ' full census mismatch')
        results[name] = actual
    base, cand = results['baseline'], results['candidate']
    require(set(base) == set(cand) and len(base) == 1035, 'incomplete window census')
    losses = {kind: [hex(int(k)) for k in base if base[k][kind] and not cand[k][kind]]
              for kind in ('normalized', 'raw')}
    gains = {kind: [hex(int(k)) for k in base if not base[k][kind] and cand[k][kind]]
             for kind in ('normalized', 'raw')}
    require(not any(losses.values()), 'baseline membership lost')
    require(gains == manifest['gains'], 'recorded gain membership differs')
    require(snapshot(root / 'programs/pump') == source, 'source changed during verification')
    require(before == {name: hashlib.sha256(path.read_bytes()).hexdigest()
                       for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]},
            'ELF changed during verification')
    report = {'verified': True, 'counts': {name: {kind: sum(v[kind] for v in rows.values())
              for kind in ('normalized', 'raw')} for name, rows in results.items()},
              'gains': gains, 'losses': losses, 'source_sha256': source['sha256'],
              'scope': 'Recorded source and complete scorer census verified against supplied ELF bytes; '
                       'this command does not rebuild, rerun runtime cases or prove whole-ELF identity.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
