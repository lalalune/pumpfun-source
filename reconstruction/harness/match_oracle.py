#!/usr/bin/env python3
"""Experiment command: 0=target matched, 1=valid build without match, 2=build/input error."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import fastbuild
import score
from original_input import copy_original_inputs
from compare_scores import load_report, compare


def bound_scoring_inputs(directory):
    """Digest the copied originals and baseline snapshot the scorer reads.

    A crate build runs arbitrary build-script code, so the build may rewrite
    the scoring inputs it is scored against; binding them by content hash
    (not mtime) detects a rewrite while a build that only touches
    timestamps is not a change. The build has no legitimate reason to touch
    this directory: its work and output directories are separate paths.
    """
    tree = {}
    for path in sorted(directory.rglob('*')):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            tree[relative] = 'symlink:' + os.readlink(path)
        elif path.is_file():
            tree[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return tree


def evaluate(source, work, output, target, kind, recipe, baseline=None):
    scoring = work / 'scoring-inputs'
    scoring.mkdir(parents=True)
    copy_original_inputs(score.BASE, scoring)
    previous = score.BASE
    score.BASE = scoring
    try:
        inventory = {w['start']: w for w in score.original_windows()}
        reference = None
        baseline_sha256 = None
        if baseline is not None:
            raw_baseline = Path(baseline).read_bytes()
            baseline_sha256 = hashlib.sha256(raw_baseline).hexdigest()
            snapshot = scoring / 'baseline.json'
            snapshot.write_bytes(raw_baseline)
            reference = load_report(snapshot)
            if set(reference) != set(inventory) or any(reference[k]['bytes'] != inventory[k]['bytes'] for k in inventory):
                raise ValueError('baseline must describe the selected original inventory and window sizes')
        if target not in inventory:
            raise ValueError('target absent from selected original inventory')
        bound = bound_scoring_inputs(scoring)
        built = fastbuild.build(source, work / 'build', output, quiet=True, recipe=recipe)
        if not built.get('ok') or built.get('runtime_valid') is False or built.get('stack_warnings'):
            result = {'status': 'error', 'build': built}
            code = 2
        elif bound_scoring_inputs(scoring) != bound:
            result = {'status': 'error', 'build': built,
                      'score_error': 'scoring inputs changed during build; refusing to score'}
            code = 2
        else:
            windows = score.score(output / 'unstripped.so')
            matched = windows[target][kind]
            result = {'status': 'pass' if matched else 'fail', 'build': built,
                      'target': target, 'kind': kind, 'window': windows[target]}
            if reference is not None:
                preservation = compare(reference, windows)
                result.update(baseline_sha256=baseline_sha256, preservation=preservation)
                matched = matched and preservation['accepted']
                result['status'] = 'pass' if matched else 'fail'
            code = 0 if matched else 1
        (output / 'verdict.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
        return code
    finally:
        score.BASE = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'work', 'out', 'sdk']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--hybrid', type=Path, help='required for the identity recipe')
    parser.add_argument('--baseline', type=Path, help='also require every baseline normalized/raw membership to survive')
    parser.add_argument('--window', type=lambda x: int(x, 0), required=True)
    parser.add_argument('--kind', choices=['normalized', 'raw'], default='normalized')
    parser.add_argument('--recipe', choices=['mac', 'identity'], default='identity')
    args = parser.parse_args()
    if args.recipe == 'identity' and args.hybrid is None:
        parser.error('--hybrid is required for identity')
    fastbuild.SDK = args.sdk.resolve()
    rustc = (args.hybrid if args.recipe == 'identity' else args.sdk) / 'rust/bin/rustc'
    fastbuild.RECIPES[args.recipe] = dict(fastbuild.RECIPES[args.recipe], rustc=rustc.resolve(), template=args.work / 'unused-template')
    score.OBJDUMP = str(fastbuild.SDK / 'llvm/bin/llvm-objdump')
    args.out.mkdir(parents=True, exist_ok=True)
    return evaluate(args.source, args.work, args.out, args.window, args.kind, args.recipe, args.baseline)


if __name__ == '__main__':
    try:
        code = main()
    except Exception as exc:
        print(f'match oracle error: {exc}', file=sys.stderr)
        code = 2
    raise SystemExit(code)
