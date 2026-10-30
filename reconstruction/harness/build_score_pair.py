#!/usr/bin/env python3
"""Build two Pump source checkouts with one harness, then enforce no lost matches."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import compare_scores
import fastbuild
import score


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_receipt(repo):
    repo = repo.resolve()
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=all', '--', 'programs/pump'])
    if dirty:
        raise ValueError('Pump source checkout must be clean')
    crate = repo / 'programs/pump'
    files = {}
    for path in sorted(crate.rglob('*')):
        if 'target' in path.relative_to(crate).parts:
            continue
        if path.is_symlink():
            raise ValueError(f'source symlink is unsupported: {path.relative_to(crate)}')
        if path.is_file():
            files[path.relative_to(crate).as_posix()] = sha(path)
    if not all(p in files for p in ('Cargo.toml', 'Cargo.lock', 'src/lib.rs')):
        raise ValueError('missing Pump crate inputs')
    return {'revision': revision, 'files': files,
            'sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def require_valid_build(result):
    if not result.get('ok') or not result.get('runtime_valid') or result.get('stack_warnings'):
        raise ValueError('build failed or reported invalid stack frames; refusing to score')


def run_pair(base, candidate, out, sdk, hybrid):
    before = {name: source_receipt(repo) for name, repo in [('base', base), ('candidate', candidate)]}
    out.mkdir(parents=True, exist_ok=False)
    fastbuild.SDK = sdk
    fastbuild.RECIPES['identity'] = {
        'triple': 'sbpf-solana-solana', 'rustc': hybrid / 'rust/bin/rustc',
        'template': out / 'no-template'}
    # Every invocation uses two separate, cold target directories and one scorer.
    fastbuild.LOCKDIR = out / 'locks'
    score.OBJDUMP = str(sdk / 'llvm/bin/llvm-objdump')
    score.BASE = out / 'scoring-inputs'
    score.BASE.mkdir()
    canonical = Path(__file__).resolve().parents[1] / 'base'
    for name in ('original.so', 'functions.tsv'):
        shutil.copyfile(canonical / name, score.BASE / name)
    receipt = {'sources': before, 'recipe': 'identity', 'cold_targets': True,
               'inputs': {name: sha(score.BASE / name) for name in ('original.so', 'functions.tsv')},
               'tools': {name: sha(Path(__file__).parent / name) for name in
                         ('build_score_pair.py', 'fastbuild.py', 'score.py', 'compare_scores.py', 'pump_physical_source_wrapper.py')},
               'sdk_inventory_sha256': sha(canonical.parent / 'toolchain/v1.44-macos-inventory.json'),
               'target_library_manifest_sha256': sha(Path(__file__).parent / 'linux144-sbpf-target-libs.sha256'),
               'compiler_sha256': sha(hybrid / 'rust/bin/rustc'),
               'objdump_sha256': sha(sdk / 'llvm/bin/llvm-objdump'), 'builds': {}}
    def save():
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    save()
    reports = {}
    try:
        for name, repo in [('base', base), ('candidate', candidate)]:
            result = fastbuild.build(repo / 'programs/pump', out / (name + '-work'), out / name,
                                     quiet=True, recipe='identity')
            # Public receipt avoids serializing local absolute output paths.
            receipt['builds'][name] = {k: v for k, v in result.items()
                                      if k not in ('unstripped', 'log')}
            save()
            require_valid_build(result)
            if source_receipt(repo) != before[name]:
                raise ValueError('source changed during build')
            windows = score.score(out / name / 'unstripped.so')
            reports[name] = windows
            (out / (name + '-score.json')).write_text(json.dumps({'windows': windows}, indent=2) + '\n')
        comparison = compare_scores.compare(reports['base'], reports['candidate'])
        receipt['comparison'] = comparison
        save()
        return 0 if comparison['accepted'] else 1
    except Exception as error:
        receipt['error'] = str(error)
        save()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, default=Path.home() / '.cache/solana/v1.44/platform-tools')
    parser.add_argument('--hybrid', type=Path, default=Path(os.environ.get('PUMP_RECON_HOME', str(Path.home() / '.cache/pumpfun-reconstruction'))) / 'toolchains/hybrid144')
    args = parser.parse_args()
    try:
        return run_pair(args.base.resolve(), args.candidate.resolve(), args.out.resolve(), args.sdk.resolve(), args.hybrid.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(2, f'build/score gate failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
