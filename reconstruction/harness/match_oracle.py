#!/usr/bin/env python3
"""Experiment command: 0=target matched, 1=valid build without match, 2=build/input error."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
try:
    import elf_symbols  # Admit lazy symbol-reader bytes before any build.
    import fastbuild
    import score
    from original_input import copy_original_inputs
    from compare_scores import load_report, compare
except Exception as exc:
    # An uncaught exception exits 1, which the command contract reads as a valid non-match.
    print(f'match oracle error: {exc}', file=sys.stderr)
    raise SystemExit(2)


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


def publish_verdict(path, text):
    """Publish the verdict without following a link planted at its path.

    Mirrors score.write_report's exclusive, unpredictable staging so a
    symlink at the destination is replaced rather than followed, while
    keeping the verdict's explicit LF line endings on every platform.
    """
    for _ in range(100):
        temporary = path.parent / f'.verdict-{os.getpid()}-{secrets.token_hex(8)}'
        try:
            stream = temporary.open('x', encoding='utf-8', newline='\n')
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError('could not create a unique verdict staging file')
    metadata = os.fstat(stream.fileno())
    identity = metadata.st_dev, metadata.st_ino
    try:
        with stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                metadata = temporary.lstat()
            except FileNotFoundError:
                pass
            else:
                if (metadata.st_dev, metadata.st_ino) == identity:
                    temporary.unlink()


def evaluate(source, work, output, target, kind, recipe, baseline=None):
    # The scoring snapshot is written beside the workspace; refuse an overlap
    # first so a rejected invocation leaves the source tree untouched.
    fastbuild.require_separate(source, work, output)
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
        publish_verdict(output / 'verdict.json', json.dumps(result, indent=2) + '\n')
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
    # Admit the paths before writing scoring inputs or outputs. fastbuild's
    # later guard cannot undo writes made by this oracle.
    source = args.source.resolve()
    for path in (args.work.resolve(), args.out.resolve()):
        if path == source or source in path.parents or path in source.parents:
            raise ValueError('source must not overlap the work or output directory')
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
