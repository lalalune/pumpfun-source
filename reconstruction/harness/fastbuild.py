#!/usr/bin/env python3
"""Fast iterative build of the main Pump crate, faithful to pump_build_verified.py --workspace-layout.

Usage: fastbuild.py --src <crate dir with Cargo.toml/Cargo.lock/src[/recovered]> --work <persistent lane work dir> [--out <dir>]

- Stages the crate as <work>/ws/programs/pump inside a one-member workspace (same split of
  [profile.release] into the workspace root as the verified builder).
- Keeps a persistent CARGO_TARGET_DIR at <work>/target so external deps compile once; only
  the main crate recompiles (lto=false, codegen-units=1, non-incremental release => output
  equals a fresh build of the same sources).
- Seeds <work>/target from the warm template (APFS clone) on first use.
- Writes <out>/unstripped.so and <out>/candidate.so (default <work>/last).
- Before compilation, archives previous outputs and their log under <out>/previous/build-*.
  Compiler failures leave no current binaries; callers must still check ok.
- Stack diagnostics return ok=false with build.log and stack_warnings. Diagnostic callers
  gated on ok (including exactsol-introspection capture.py) consequently skip IR extraction.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, tomllib, fcntl, tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
SC = H.parent
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
# Generated toolchain, dependency caches and build-slot locks live outside the repository so every
# worktree shares them (see reconstruction/toolchain/bootstrap.py).
CACHE = Path(os.environ.get('PUMP_RECON_HOME', str(Path.home() / '.cache/pumpfun-reconstruction')))
# Recipes: 'mac' = installed macOS v1.44 SDK, triple sbf-solana-solana (Codex harness default);
# 'identity' = same macOS rustc binary with the official Linux x86_64 v1.44 target libraries, triple
# sbpf-solana-solana (the original's toolchain identity, proven by TypeId constants; identity-01).
RECIPES = {
    'mac': {'triple': 'sbf-solana-solana', 'rustc': SDK / 'rust/bin/rustc', 'template': CACHE / 'template-target'},
    'identity': {'triple': 'sbpf-solana-solana', 'rustc': CACHE / 'toolchains/hybrid144/rust/bin/rustc', 'template': CACHE / 'template-target-sbpf'},
}
DEFAULT_RECIPE = os.environ.get('PUMP_RECIPE', 'identity')
# Shared with the peer Claude session's lanes so total concurrent SBF builds stay capped.
LOCKDIR = Path(os.environ.get('PUMP_BUILD_LOCKDIR', str(CACHE / 'locks')))  # durable; shared with peer sessions
SLOTS = int(os.environ.get('PUMP_BUILD_SLOTS', '6'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def stage(src: Path, ws: Path):
    text = (src / 'Cargo.toml').read_text()
    parsed = tomllib.loads(text)
    assert parsed.get('workspace') == {} and set(parsed.get('profile', {})) == {'release'}, 'unsupported manifest layout'
    ps = text.index('[profile.release]'); wsi = text.index('[workspace]')
    assert ps < wsi and not text[wsi + len('[workspace]'):].strip()
    profile = text[ps:wsi].strip() + '\n'
    crate_text = text[:ps].rstrip() + '\n'
    crate = ws / 'programs/pump'
    crate.mkdir(parents=True, exist_ok=True)
    # mirror .rs sources (+ any non-target files) with rsync --checksum so unchanged files keep mtimes;
    # only the crate-root manifest/lock are excluded (rewritten below), nested path crates keep their Cargo.toml
    subprocess.run(['rsync', '-a', '--checksum', '--delete',
                    '--exclude', 'target', '--exclude', '/Cargo.toml', '--exclude', '/Cargo.lock',
                    str(src) + '/', str(crate) + '/'], check=True)
    def put(p, t):
        if not p.exists() or p.read_text() != t:
            p.write_text(t)
    put(crate / 'Cargo.toml', crate_text)
    put(ws / 'Cargo.toml', '[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + profile)
    lock = (src / 'Cargo.lock').read_text()
    put(ws / 'Cargo.lock', lock)
    return crate


def acquire_slot():
    LOCKDIR.mkdir(parents=True, exist_ok=True)
    while True:
        for i in range(SLOTS):
            f = open(LOCKDIR / f'sbf{i}.lock', 'w')  # same names as the peer's `sbf_lock.py --name sbf`
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return f
            except BlockingIOError:
                f.close()
        time.sleep(0.5)


def archive_previous_outputs(out: Path):
    """Keep old evidence separate from the next attempt's canonical output paths."""
    names = ('unstripped.so', 'candidate.so', 'build.log')
    present = [out / name for name in names
               if (out / name).exists() or (out / name).is_symlink()]
    if not present:
        return
    previous = out / 'previous'
    previous.mkdir(exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix='build-', dir=previous))
    for path in present:
        path.rename(archive / path.name)


def build(src: Path, work: Path, out: Path, quiet=False, recipe=None):
    recipe = recipe or DEFAULT_RECIPE
    R = RECIPES[recipe]; triple = R['triple']
    src = src.resolve(); work = work.resolve(); out = out.resolve()
    work.mkdir(parents=True, exist_ok=True)
    ws = work / 'ws'
    crate = stage(src, ws)
    target = work / ('target' if recipe == 'mac' else f'target-{recipe}')
    if not target.exists() and R['template'].exists():
        subprocess.run(['cp', '-cRp', str(R['template']), str(target)], check=True)
    env = os.environ.copy()
    env.pop('CARGO_BUILD_TARGET_DIR', None)
    reg = Path.home() / '.cargo'
    env.update(
        RUSTC_WRAPPER=str(H / 'pump_physical_source_wrapper.py'),
        PUMP_LOGICAL_REGISTRY_SRC=str(reg / 'registry/src'),
        CARGO_HOME=str(reg),
        CARGO_TARGET_DIR=str(target),
        CARGO_BUILD_JOBS=os.environ.get('CARGO_BUILD_JOBS', '2'),
        RUSTC=str(R['rustc']),
        CC=str(SDK / 'llvm/bin/clang'),
        AR=str(SDK / 'llvm/bin/llvm-ar'),
        OBJDUMP=str(SDK / 'llvm/bin/llvm-objdump'),
        OBJCOPY=str(SDK / 'llvm/bin/llvm-objcopy'),
    )
    env['CARGO_TARGET_' + triple.upper().replace('-', '_') + '_RUSTFLAGS'] = '-Zremap-cwd-prefix='
    env.pop('RUSTFLAGS', None); env.pop('CARGO_ENCODED_RUSTFLAGS', None)
    cmd = [str(SDK / 'rust/bin/cargo'), 'build', '--manifest-path', str(crate / 'Cargo.toml'), '--release',
           '--target', triple, '--locked', '--offline']
    out.mkdir(parents=True, exist_ok=True)
    archive_previous_outputs(out)
    # Never trust mtime freshness for the main crate (rsync -a keeps source mtimes, so cargo could
    # otherwise reuse a stale pump artifact): drop its fingerprints and outputs so it always recompiles.
    for fp in list(target.glob('*/release/.fingerprint/pump-recovered-*')) + list(target.glob('release/.fingerprint/pump-recovered-*')):
        shutil.rmtree(fp, ignore_errors=True)
    for so in target.glob('*/release/pump_recovered.so'):
        so.unlink()
    slot = acquire_slot()
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=ws, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    finally:
        slot.close()
    dt = time.time() - t0
    (out / 'build.log').write_text(r.stdout)
    if r.returncode != 0:
        if not quiet:
            sys.stdout.write(r.stdout[-6000:])
        return {'ok': False, 'recipe': recipe, 'seconds': round(dt, 1), 'log': str(out / 'build.log')}
    # SBF frames are 4 KiB: any "Stack offset ... exceeded max offset" warning means the program can fault at
    # runtime (the original runs, so its functions fit). Such a build must never be delivered or integrated.
    stack = [l.strip() for l in r.stdout.splitlines() if 'exceeded max offset' in l]
    if stack and not quiet:
        sys.stderr.write('STACK OVERFLOW RISK (runtime-invalid build):\n  ' + '\n  '.join(stack) + '\n')
    if stack:
        return {'ok': False, 'runtime_valid': False, 'stack_warnings': stack,
                'recipe': recipe, 'triple': triple, 'seconds': round(dt, 1),
                'log': str(out / 'build.log')}
    built = target / triple / 'release/pump_recovered.so'
    shutil.copy2(built, out / 'unstripped.so')
    subprocess.run([str(SDK / 'llvm/bin/llvm-objcopy'), '--strip-all', str(built), str(out / 'candidate.so')], check=True)
    return {'ok': True, 'runtime_valid': not stack, 'stack_warnings': stack, 'recipe': recipe, 'triple': triple, 'seconds': round(dt, 1), 'unstripped': str(out / 'unstripped.so'),
            'unstripped_sha256': sha(out / 'unstripped.so'), 'candidate_sha256': sha(out / 'candidate.so')}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--recipe', choices=sorted(RECIPES), default=DEFAULT_RECIPE, help='identity (default) = Linux v1.44 sbpf target libs; mac = Codex harness recipe')
    a = ap.parse_args()
    res = build(a.src, a.work, a.out or (a.work / 'last'), recipe=a.recipe)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res['ok'] else 1)
