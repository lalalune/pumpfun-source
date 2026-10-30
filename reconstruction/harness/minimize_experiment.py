#!/usr/bin/env python3
"""Reduce an ordered list of patch units while retaining an experiment predicate."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from experiment_runner import run_trial, atomic_json, digest, stage_ignore, manifest


def minimize(count, evaluate, budget, wanted='pass'):
    if count < 1 or budget < 1 or wanted not in ('pass', 'fail'): raise ValueError('invalid minimization options')
    cache = {}
    def test(items):
        key = tuple(items)
        if key not in cache:
            if len(cache) >= budget: return None
            value = evaluate(list(key))
            if value not in ('pass', 'fail', 'error'): raise ValueError('invalid oracle status')
            cache[key] = value
        return cache[key]
    current = list(range(count))
    if test(current) != wanted: return {'status': 'initial-predicate-not-met', 'selected': current, 'one_minimal': False}
    if test([]) == wanted: current = []
    partitions = 2
    while len(current) >= 2 and len(cache) < budget:
        width = (len(current) + partitions - 1) // partitions
        reduced = False
        for start in range(0, len(current), width):
            subset = current[:start] + current[start + width:]
            if test(subset) == wanted:
                current = subset; partitions = max(2, partitions - 1); reduced = True; break
        if not reduced:
            if partitions >= len(current): break
            partitions = min(len(current), partitions * 2)
    one_minimal = all(test(current[:i] + current[i + 1:]) in ({'pass', 'fail'} - {wanted}) for i in range(len(current)))
    return {'status': 'complete' if one_minimal else 'bounded-result', 'selected': current,
            'one_minimal': one_minimal, 'wanted': wanted,
            'tested': [{'selected': list(key), 'status': value} for key, value in cache.items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--patches', type=Path, required=True, help='JSON array of ordered patch-file paths')
    parser.add_argument('--oracle', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--want', choices=['pass', 'fail'], default='pass')
    parser.add_argument('--max-trials', type=int, default=30)
    args = parser.parse_args()
    args.source = args.source.resolve(); args.out = args.out.resolve()
    if args.source == args.out or args.source in args.out.parents or args.out in args.source.parents:
        parser.error('source and output must be separate trees')
    source_identity = manifest(args.source)
    paths = [Path(p).resolve() for p in json.loads(args.patches.read_text())]
    patches = [p.read_bytes() for p in paths]
    config = json.loads(args.oracle.read_text())
    args.out.mkdir(parents=True, exist_ok=True)
    patch_errors = []
    def evaluate(selected):
        with tempfile.TemporaryDirectory(prefix='reduce-source-', dir=args.out) as temporary:
            stage = Path(temporary) / 'source'
            shutil.copytree(args.source, stage, ignore=stage_ignore(args.source))
            if manifest(stage) != source_identity or manifest(args.source) != source_identity:
                raise ValueError('base source changed during minimization')
            subprocess.run(['git', '-C', str(stage), 'init', '-q'], check=True)
            for index in selected:
                applied = subprocess.run(['git', '-C', str(stage), 'apply', '--whitespace=nowarn', '-'], input=patches[index], capture_output=True)
                if applied.returncode:
                    patch_errors.append({'selected': selected, 'patch_index': index, 'stderr': applied.stderr.decode(errors='replace')[-4000:]})
                    return 'error'
            key = digest(json.dumps(selected).encode())[:16]
            return run_trial(stage, config['command'], args.out / 'trials' / key,
                             config.get('inputs', []), config.get('timeout', 300))['status']
    result = minimize(len(paths), evaluate, args.max_trials, args.want)
    result['source'] = source_identity
    result['patch_errors'] = patch_errors
    result['patches'] = [{'index': i, 'sha256': digest(raw)} for i, raw in enumerate(patches)]
    atomic_json(args.out / 'minimized.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'complete' else 2


if __name__ == '__main__': raise SystemExit(main())
