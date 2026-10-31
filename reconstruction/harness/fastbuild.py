#!/usr/bin/env python3
"""Fast iterative build of the main Pump crate, faithful to pump_build_verified.py --workspace-layout.

Usage: fastbuild.py --src <crate dir with Cargo.toml/Cargo.lock/src[/recovered]> --work <persistent lane work dir> [--out <dir>]

- Stages the crate as <work>/ws/programs/pump inside a one-member workspace (same split of
  [profile.release] into the workspace root as the verified builder).
- Keeps a persistent CARGO_TARGET_DIR at <work>/target so external deps compile once; only
  the main crate and the path crates nested in it (pump-token-ext) recompile (lto=false,
  codegen-units=1, non-incremental release => output equals a fresh build of the same sources).
- Seeds <work>/target from the warm template (APFS clone) on first use.
- Writes <out>/unstripped.so and <out>/candidate.so (default <work>/last).
  An explicit output directory may equal the work directory, including with a pinned link script.
- Before compilation, archives previous outputs and their log under <out>/previous/build-*.
  Compiler/strip failures install no binaries; callers must still check ok.
  Each binary is installed without replacement. If a later publication step fails,
  an earlier complete binary remains, but no successful build receipt is returned.
- Concurrent trials must use distinct workspaces and output directories. A busy output is
  rejected before staging/publication, so its binary and source receipt cannot come from different trials.
- A crate carrying link/ordered.ld (a pinned link order, see link_order.py) is linked with that
  script in place of the SBF default one; the result reports its sha256 and selector counts and
  fails unless the linker hook ran in this build.
- Stack diagnostics return ok=false with build.log and stack_warnings. Diagnostic callers
  gated on ok (including exactsol-introspection capture.py) consequently skip IR extraction.
- Cargo manifests, lockfiles and saved compiler logs use UTF-8 independently of the host locale.
  Non-UTF-8 consoles escape unrepresentable diagnostic characters without changing the saved log.
"""
import argparse, hashlib, io, json, os, re, shutil, subprocess, sys, time, tomllib, fcntl, tempfile
from contextlib import contextmanager
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling modules under -I / load-by-path
from build_process import run_compiler, validate_timeout
from source_inputs import snapshot, assert_unchanged
import link_order

H = Path(__file__).resolve().parent
SC = H.parent
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
# Generated toolchain, dependency caches and build-slot locks live outside the repository so every
# worktree shares them (see reconstruction/toolchain/bootstrap.py).
# Cargo runs from the staged workspace; anchor relative overrides without resolving symlinks.
# APFS clonefile (-c) keeps the warm template cheap on macOS; GNU cp rejects -c.
CLONE = ['cp', '-cRp'] if sys.platform == 'darwin' else ['cp', '-a']
CACHE = Path(os.environ.get('PUMP_RECON_HOME', str(Path.home() / '.cache/pumpfun-reconstruction'))).absolute()
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


def echo_diagnostics(text):
    # Keep the saved log in UTF-8; a legacy console may need escaped characters.
    encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
    sys.stdout.write(text.encode(encoding, errors='backslashreplace').decode(encoding))


def table_start(text, name):
    """Find a real literal table header, excluding comments and string contents."""
    pattern = r'(?m)^[ \t]*\[' + re.escape(name) + r'\][ \t]*(?:#[^\n]*)?$'
    for match in re.finditer(pattern, text):
        try:
            # A header-looking line inside a multiline value has an incomplete
            # TOML prefix; a real table starts after complete preceding values.
            tomllib.loads(text[:match.start()])
        except tomllib.TOMLDecodeError:
            continue
        return match.start()
    raise ValueError('missing literal manifest table: ' + name)


def reject_cargo_configs(ws: Path):
    """Refuse the unrecorded config files Cargo merges over the staged release recipe."""
    # Cargo runs from ws: it reads every parent of ws and its CARGO_HOME, ~/.cargo.
    directories = {directory / '.cargo' for directory in (ws.absolute(), *ws.absolute().parents)}
    directories.add(Path.home() / '.cargo')
    configs = [directory / name for directory in directories for name in ('config', 'config.toml')
               if os.path.lexists(directory / name)]
    if configs:
        raise ValueError('unreviewed Cargo config: ' + ', '.join(map(str, sorted(configs))))


def stage(src: Path, ws: Path, expected_inputs=None):
    expected_inputs = snapshot(src) if expected_inputs is None else expected_inputs
    reject_cargo_configs(ws)

    def admitted_text(name):
        data = (src / name).read_bytes()
        expected = next(row for row in expected_inputs['files'] if row['path'] == name)
        if hashlib.sha256(data).hexdigest() != expected['sha256']:
            raise ValueError('source metadata differs from admitted inputs: ' + name)
        # Preserve read_text's universal-newline handling of the admitted bytes.
        return io.StringIO(data.decode('utf-8'), newline=None).read()

    text = admitted_text('Cargo.toml')
    parsed = tomllib.loads(text)
    if parsed.get('workspace') != {} or set(parsed.get('profile', {})) != {'release'}:
        raise ValueError('unsupported manifest layout')
    ps = table_start(text, 'profile.release'); wsi = table_start(text, 'workspace')
    if ps >= wsi or tomllib.loads(text[wsi:]) != {'workspace': {}}:
        raise ValueError('expected release profile followed by a final empty workspace table')
    profile = text[ps:wsi].strip() + '\n'
    crate_text = text[:ps].rstrip() + '\n'
    lock = admitted_text('Cargo.lock')
    crate = ws / 'programs/pump'
    # Reused staging paths must not redirect rsync or the metadata rewrites
    # into the source (or an earlier workspace). Check before any writes.
    for directory in (ws, ws / 'programs', crate):
        if directory.is_symlink():
            raise ValueError('staging directory must not be a symlink: ' + str(directory))
    for path in (crate / 'Cargo.toml', ws / 'Cargo.toml', ws / 'Cargo.lock'):
        if path.is_symlink() or (path.exists() and
                (not path.is_file() or path.stat().st_nlink != 1)):
            raise ValueError('staging metadata must be an ordinary file with one link: ' + str(path))
    crate.mkdir(parents=True, exist_ok=True)
    # Exclude only the crate-root build directory; nested target directories can contain source.
    # Mirror inputs with rsync --checksum so unchanged files keep mtimes;
    # only the crate-root manifest/lock are excluded (rewritten below), nested path crates keep their Cargo.toml
    subprocess.run(['rsync', '-a', '--checksum', '--delete',
                    '--exclude', '/target/', '--exclude', '/Cargo.toml',
                    # Sender-only hiding lets --delete remove a stale crate-local lock.
                    # The admitted root lock is generated at the workspace root below.
                    '--filter', 'H /Cargo.lock',
                    str(src) + '/', str(crate) + '/'], check=True)
    # Cargo metadata is generated from admitted buffers below. Bind every other
    # selected input in the copy, including nested path-crate Cargo metadata.
    generated = {'Cargo.toml', 'Cargo.lock'}
    expected = {row['path']: row for row in expected_inputs['files'] if row['path'] not in generated}
    staged_inputs = snapshot(crate)
    actual = {row['path']: row for row in staged_inputs['files'] if row['path'] != 'Cargo.toml'}
    changed_dirs = set(staged_inputs['directories']) ^ set(expected_inputs['directories'])
    if actual != expected or changed_dirs:
        changed_files = {name for name in actual.keys() | expected.keys() if actual.get(name) != expected.get(name)}
        changed = sorted(changed_files | changed_dirs)
        raise ValueError('staged source inputs differ from admitted inputs: ' + ', '.join(changed[:10]))
    def put(p, t):
        if not p.exists() or p.read_text(encoding='utf-8') != t:
            p.write_text(t, encoding='utf-8', newline='\n')
    put(crate / 'Cargo.toml', crate_text)
    put(ws / 'Cargo.toml', '[workspace]\nmembers = ["programs/pump"]\nresolver = "2"\n\n' + profile)
    put(ws / 'Cargo.lock', lock)
    return crate


def local_packages(crate: Path):
    """Package names of the staged crate and of every path crate nested in it."""
    names = set()
    for manifest in crate.rglob('Cargo.toml'):
        name = tomllib.loads(manifest.read_text(encoding='utf-8')).get('package', {}).get('name')
        if name:
            names.add(name)
    return names


def validate_slots():
    if SLOTS <= 0:
        raise ValueError('PUMP_BUILD_SLOTS must be a positive integer')


def acquire_slot():
    validate_slots()
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


@contextmanager
def workspace_lock(work: Path):
    """Protect staging, target invalidation and publication for one work directory."""
    work = work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    # Keep the inode after releasing it; unlinking would permit split locks.
    with (work / '.fastbuild.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f'build workspace already in use: {work}') from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


@contextmanager
def output_lock(out: Path):
    """Serialize a canonical output directory even across distinct workspaces."""
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    # Keep the lock beside outputs, so it is not part of the measured artifacts.
    # As with the workspace lock, retain its inode after releasing it.
    with (out.parent / f'.{out.name}.fastbuild-output.lock').open('a+b') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f'build output already in use: {out}') from error
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def archive_previous_outputs(out: Path):
    """Keep old evidence separate from the next attempt's canonical output paths."""
    names = ('unstripped.so', 'candidate.so', 'build.log', 'link-receipt.json', 'link.map', 'source-inputs.json')
    present = [out / name for name in names
               if (out / name).exists() or (out / name).is_symlink()]
    if not present:
        return
    previous = out / 'previous'
    previous.mkdir(exist_ok=True)
    archive = Path(tempfile.mkdtemp(prefix='build-', dir=previous))
    for path in present:
        path.rename(archive / path.name)


def build(src: Path, work: Path, out: Path, quiet=False, recipe=None, timeout=None):
    validate_timeout(timeout)
    validate_slots()
    src = src.resolve(); work = work.resolve(); out = out.resolve()
    # Reject overlap before workspace_lock can create a directory or lock in
    # the source tree (and thereby change its source-input receipt). The
    # output directory must not contain the source either: publishing into a
    # parent of src archives and writes inside the tree that holds it.
    if (src == work or src in work.parents or work in src.parents
            or src == out or src in out.parents or out in src.parents):
        raise ValueError('source must not overlap the build workspace or contain output')
    # Staging uses rsync --delete before prior outputs are archived.
    staged = (work / 'ws/programs/pump').resolve()
    if out == staged or staged in out.parents:
        raise ValueError('output must not be inside the staged source tree')
    with workspace_lock(work):
        with output_lock(out):
            return _build_locked(src, work, out, quiet=quiet, recipe=recipe, timeout=timeout)


def publish_binary(source, destination):
    """Install one complete binary without replacing an unexpected late file."""
    if os.name == 'nt':
        os.rename(source, destination)
    else:
        os.link(source, destination)


def _build_locked(src: Path, work: Path, out: Path, quiet=False, recipe=None, timeout=None):

    recipe = recipe or DEFAULT_RECIPE
    R = RECIPES[recipe]; triple = R['triple']
    source_inputs = snapshot(src)
    work.mkdir(parents=True, exist_ok=True)
    ws = work / 'ws'
    crate = stage(src, ws, expected_inputs=source_inputs)
    assert_unchanged(src, source_inputs)
    manifest = tomllib.loads((crate / 'Cargo.toml').read_text(encoding='utf-8'))
    library = manifest.get('lib', {}).get('name', manifest['package']['name'].replace('-', '_'))
    target = work / ('target' if recipe == 'mac' else f'target-{recipe}')
    if not target.exists() and R['template'].exists():
        subprocess.run(CLONE + [str(R['template']), str(target)], check=True)
    env = os.environ.copy()
    env.pop('CARGO_BUILD_TARGET_DIR', None)
    reg = Path.home() / '.cargo'
    env.update(
        RUSTC_WRAPPER=str(H / 'pump_physical_source_wrapper.sh'),
        PUMP_RECON_PYTHON=sys.executable,
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
    # These outrank the staged release recipe, replace its target/host linker,
    # or wrap only the local crates. Keep linker choice in the pinned recipe.
    for name in list(env):
        if (name.startswith('CARGO_PROFILE_')
                or (name.startswith('CARGO_TARGET_') and name.endswith('_LINKER'))
                or name in (
                'CARGO_INCREMENTAL', 'CARGO_BUILD_INCREMENTAL',
                'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER')):
            del env[name]
    receipt = work / 'link-receipt.json'
    link_env, link_record = link_order.configure(crate, R['rustc'], receipt)
    env.update(link_env)
    cmd = [str(SDK / 'rust/bin/cargo'), 'build', '--manifest-path', str(crate / 'Cargo.toml'), '--release',
           '--target', triple, '--locked', '--offline']
    out.mkdir(parents=True, exist_ok=True)
    archive_previous_outputs(out)
    # If out == work, these are previous published evidence. Archive them
    # before clearing the transient linker paths for the next compiler run.
    receipt.unlink(missing_ok=True)
    receipt.with_name('link.map').unlink(missing_ok=True)
    (out / 'source-inputs.json').write_text(json.dumps(source_inputs, indent=2) + '\n',
                                            encoding='utf-8', newline='\n')
    # Never trust mtime freshness for local crates (rsync -a keeps source mtimes, so cargo could
    # otherwise reuse a stale pump artifact): drop their fingerprints (and the main output) so they
    # always recompile. This includes path crates nested in the staged crate, such as pump-token-ext;
    # otherwise restaging older sources links the previous trial's library.
    for name in {'pump-recovered'} | local_packages(crate):
        for fp in list(target.glob(f'*/release/.fingerprint/{name}-*')) + list(target.glob(f'release/.fingerprint/{name}-*')):
            shutil.rmtree(fp, ignore_errors=True)
    for so in target.glob('*/release/*.so'):
        if so.name == f'{library}.so':
            so.unlink()
    slot = acquire_slot()
    t0 = time.time()
    try:
        r, timed_out = run_compiler(cmd, cwd=ws, env=env, timeout=timeout)
    finally:
        slot.close()
    dt = time.time() - t0
    (out / 'build.log').write_text(r.stdout, encoding='utf-8', newline='\n')
    if timed_out or r.returncode != 0:
        if not quiet:
            echo_diagnostics(r.stdout[-6000:])
        return {'ok': False, 'timed_out': timed_out, 'source_sha256': source_inputs['sha256'], 'recipe': recipe, 'seconds': round(dt, 1), 'log': str(out / 'build.log')}
    # SBF frames are 4 KiB: any "Stack offset ... exceeded max offset" warning means the program can fault at
    # runtime (the original runs, so its functions fit). Such a build must never be delivered or integrated.
    stack = [l.strip() for l in r.stdout.splitlines() if 'exceeded max offset' in l]
    if stack and not quiet:
        sys.stderr.write('STACK OVERFLOW RISK (runtime-invalid build):\n  ' + '\n  '.join(stack) + '\n')
    if stack:
        return {'ok': False, 'runtime_valid': False, 'stack_warnings': stack,
                'source_sha256': source_inputs['sha256'],
                'recipe': recipe, 'triple': triple, 'seconds': round(dt, 1),
                'log': str(out / 'build.log')}
    if link_record:
        if not receipt.is_file():
            raise RuntimeError('pinned link script configured but the linker hook did not run')
        got = json.loads(receipt.read_text())
        if got['script_sha256'] != link_record['script_sha256'] or got['lld_sha256'] != link_record['lld_sha256']:
            raise RuntimeError('link receipt does not match the pinned link script')
        if out != work:  # Otherwise the linker already wrote the output files.
            shutil.copy2(receipt, out / 'link-receipt.json')
            shutil.copy2(receipt.with_name('link.map'), out / 'link.map')
    built = target / triple / 'release' / f'{library}.so'
    with tempfile.TemporaryDirectory(prefix='.publish-', dir=out) as temporary:
        pending = Path(temporary)
        shutil.copy2(built, pending / 'unstripped.so')
        try:
            subprocess.run([str(SDK / 'llvm/bin/llvm-objcopy'), '--strip-all', str(pending / 'unstripped.so'),
                            str(pending / 'candidate.so')], check=True,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
            hashes = {name: sha(pending / name) for name in ('unstripped.so', 'candidate.so')}
            for name in hashes:
                publish_binary(pending / name, out / name)
            if any(sha(out / name) != digest for name, digest in hashes.items()):
                raise ValueError('published binary changed before build receipt')
        except BaseException as error:
            # A late writer may own either destination. Keep any complete binary
            # already installed; a failing build never returns an accepted receipt.
            try:
                with (out / 'build.log').open('a', encoding='utf-8') as log:
                    log.write('\nBinary publication failed: ' + str(error) + '\n')
                    for detail in (getattr(error, 'stdout', None), getattr(error, 'stderr', None)):
                        if detail:
                            log.write(detail.decode('utf-8', errors='replace') if isinstance(detail, bytes) else detail)
            except OSError as logging_error:
                error.add_note('Could not append build log: ' + str(logging_error))
            raise
    return {'ok': True, 'source_sha256': source_inputs['sha256'], 'link_order': link_record, 'runtime_valid': not stack, 'stack_warnings': stack, 'recipe': recipe, 'triple': triple, 'seconds': round(dt, 1), 'unstripped': str(out / 'unstripped.so'),
            'unstripped_sha256': hashes['unstripped.so'], 'candidate_sha256': hashes['candidate.so']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--recipe', choices=sorted(RECIPES), default=DEFAULT_RECIPE, help='identity (default) = Linux v1.44 sbpf target libs; mac = Codex harness recipe')
    ap.add_argument('--timeout', type=float, help='compiler execution deadline in seconds (excludes staging and slot wait)')
    a = ap.parse_args()
    try:
        validate_timeout(a.timeout)
    except ValueError as error:
        ap.error(str(error))
    res = build(a.src, a.work, a.out or (a.work / 'last'), recipe=a.recipe, timeout=a.timeout)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res['ok'] else 1)
