#!/usr/bin/env python3
"""Experiment command: 0=target matched, 1=valid build without match, 2=build/input error."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import fastbuild
import score


def evaluate(source, work, output, target, kind, recipe):
    scoring = work / 'scoring-inputs'
    scoring.mkdir(parents=True)
    for name in ['original.so', 'functions.tsv']:
        shutil.copyfile(score.BASE / name, scoring / name)
    previous = score.BASE
    score.BASE = scoring
    try:
        if target not in {w['start'] for w in score.original_windows()}:
            raise ValueError('target absent from selected original inventory')
        built = fastbuild.build(source, work / 'build', output, quiet=True, recipe=recipe)
        if not built.get('ok') or built.get('runtime_valid') is False or built.get('stack_warnings'):
            result = {'status': 'error', 'build': built}
            code = 2
        else:
            windows = score.score(output / 'unstripped.so')
            matched = windows[target][kind]
            result = {'status': 'pass' if matched else 'fail', 'build': built,
                      'target': target, 'kind': kind, 'window': windows[target]}
            code = 0 if matched else 1
        (output / 'verdict.json').write_text(json.dumps(result, indent=2) + '\n')
        return code
    finally:
        score.BASE = previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['source', 'work', 'out', 'sdk']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--hybrid', type=Path, help='required for the identity recipe')
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
    return evaluate(args.source, args.work, args.out, args.window, args.kind, args.recipe)


if __name__ == '__main__':
    try:
        code = main()
    except Exception as exc:
        print(f'match oracle error: {exc}', file=sys.stderr)
        code = 2
    raise SystemExit(code)
