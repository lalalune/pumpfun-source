#!/usr/bin/env python3
"""Build two Pump source checkouts with one harness, then enforce no lost matches."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

import compare_scores
import elf_symbols  # Admit lazy symbol-reader bytes before any build.
import fastbuild
import score
from original_input import copy_original_inputs
from source_inputs import snapshot
from build_process import validate_timeout


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _reject_directory_link(path):
    path = Path(path)
    if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
        raise ValueError('source directory symlinks and other directory links are not supported')


def source_receipt(repo):
    repo = Path(repo)
    for entry in (repo, repo / 'programs', repo / 'programs/pump'):
        _reject_directory_link(entry)
    repo = repo.resolve(strict=True)
    # -C does not override repository routing inherited from a Git hook/shell.
    # All receipt queries must describe this explicitly selected checkout.
    git_env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith('GIT_')}
    # Repository paths use the filesystem codec, independently of text locale.
    toplevel = os.fsdecode(subprocess.check_output(
        ['git', '-C', str(repo), 'rev-parse', '--show-toplevel'], env=git_env)).rstrip('\r\n')
    if not Path(toplevel).samefile(repo):
        raise ValueError('Pump source checkout must be a Git worktree root')
    revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                                      text=True, env=git_env).strip()
    dirty = subprocess.check_output(
        ['git', '-C', str(repo), 'status', '--porcelain=v1', '-z',
         '--untracked-files=all', '--ignored=traditional', '--', 'programs/pump'], env=git_env)
    if any(not entry.startswith(b'!! programs/pump/target/')
           for entry in dirty.split(b'\0') if entry):
        raise ValueError('Pump source checkout must be clean')
    crate = repo / 'programs/pump'
    source = snapshot(crate)
    paths = {row['path'] for row in source['files']}
    if not {'Cargo.toml', 'Cargo.lock', 'src/lib.rs'} <= paths:
        raise ValueError('missing Pump crate inputs')
    return {'revision': revision, **source}


def require_valid_build(result):
    if not result.get('ok') or not result.get('runtime_valid') or result.get('stack_warnings'):
        raise ValueError('build failed or reported invalid stack frames; refusing to score')
    if not result.get('unstripped_sha256'):
        raise ValueError('build report has no published digest; refusing to score')


def target_libraries(hybrid):
    """Digest every sbpf target library the compiler can link.

    linux144-sbpf-target-libs.sha256 pins the list of libraries, not their
    bytes: a replaced rlib keeps the file name, changes the linked artefact,
    and leaves the manifest digest and the before/after binding identical.
    """
    library = Path(hybrid) / 'rust/lib/rustlib/sbpf-solana-solana/lib'
    return {path.name: sha(path) for path in sorted(library.glob('*.rlib'))}


def bound_inputs(scoring_inputs, sdk, hybrid):
    canonical = Path(__file__).resolve().parents[1] / 'base'
    return {'inputs': {name: sha(scoring_inputs / name) for name in ('original.so', 'functions.tsv')},
            'tools': {name: sha(Path(__file__).parent / name) for name in
                      ('build_score_pair.py', 'fastbuild.py', 'score.py', 'original_input.py', 'compare_scores.py', 'pump_physical_source_wrapper.py',
                          'link_order.py', 'pump_link_rustc.py', 'pump_link_lld.py',
                          'pump_link_rustc.sh', 'pump_link_lld.sh', 'pump_physical_source_wrapper.sh', 'sbf_default.ld',
                          'build_process.py', 'elf_symbols.py', 'instruction_stream.py',
                          'llvm_tools.py', 'score_admission.py', 'source_inputs.py')},
            'sdk_inventory_sha256': sha(canonical.parent / 'toolchain/v1.44-macos-inventory.json'),
            'target_library_manifest_sha256': sha(Path(__file__).parent / 'linux144-sbpf-target-libs.sha256'),
            'target_libraries': target_libraries(hybrid),
            'compiler_sha256': sha(hybrid / 'rust/bin/rustc'),
            'cargo_sha256': sha(sdk / 'rust/bin/cargo'),
            'clang_sha256': sha(sdk / 'llvm/bin/clang'),
            'objdump_sha256': sha(sdk / 'llvm/bin/llvm-objdump'),
            'objcopy_sha256': sha(sdk / 'llvm/bin/llvm-objcopy')}


def run_pair(base, candidate, out, sdk, hybrid, timeout=None):
    validate_timeout(timeout)
    missing = object()
    config = [(fastbuild, 'SDK'), (fastbuild, 'LOCKDIR'), (score, 'BASE'), (score, 'OBJDUMP')]
    saved = [(module, name, getattr(module, name, missing)) for module, name in config]
    recipe = fastbuild.RECIPES['identity']
    try:
        return _run_pair(base, candidate, out, sdk, hybrid, timeout)
    finally:
        fastbuild.RECIPES['identity'] = recipe
        for module, name, value in saved:
            if value is missing:
                module.__dict__.pop(name, None)
            else:
                setattr(module, name, value)


def _run_pair(base, candidate, out, sdk, hybrid, timeout):
    # Admit the canonical output before creating scoring inputs or receipts.
    # fastbuild's later guard cannot undo writes made by this coordinator.
    out = out.resolve()
    for repo in (base, candidate):
        source = (repo / 'programs/pump').resolve()
        if fastbuild.contains_path(source, out) or fastbuild.contains_path(out, source):
            raise ValueError('output must not overlap a Pump source tree')
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
    copy_original_inputs(canonical, score.BASE)
    binding = bound_inputs(score.BASE, sdk, hybrid)
    receipt = {'sources': before, 'recipe': 'identity', 'cold_targets': True,
               **binding, 'builds': {}}
    def save():
        (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n',
                                         encoding='utf-8', newline='\n')
    save()
    reports = {}
    try:
        for name, repo in [('base', base), ('candidate', candidate)]:
            result = fastbuild.build(repo / 'programs/pump', out / (name + '-work'), out / name,
                                     quiet=True, recipe='identity', timeout=timeout)
            # Public receipt avoids serializing local absolute output paths.
            receipt['builds'][name] = {k: v for k, v in result.items()
                                      if k not in ('unstripped', 'log')}
            save()
            require_valid_build(result)
            if source_receipt(repo) != before[name]:
                raise ValueError('source changed during build')
            windows = score.score(out / name / 'unstripped.so', result['unstripped_sha256'])
            reports[name] = windows
            (out / (name + '-score.json')).write_text(
                json.dumps({'windows': windows}, indent=2) + '\n',
                encoding='utf-8', newline='\n')
        # The candidate build may have changed the base tree or any previously bound tool.
        if any(source_receipt(repo) != before[name]
               for name, repo in [('base', base), ('candidate', candidate)]):
            raise ValueError('source changed during paired build')
        if bound_inputs(score.BASE, sdk, hybrid) != binding:
            raise ValueError('bound tool or scoring input changed during paired build')
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
    parser.add_argument('--timeout', type=float, help='compiler deadline per build in seconds')
    args = parser.parse_args()
    try:
        for repo in (args.base, args.candidate):
            _reject_directory_link(repo)
        return run_pair(args.base.resolve(), args.candidate.resolve(), args.out.resolve(), args.sdk.resolve(), args.hybrid.resolve(), timeout=args.timeout)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(2, f'build/score gate failed: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
