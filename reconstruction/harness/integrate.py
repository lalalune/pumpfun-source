#!/usr/bin/env python3
"""Compose several delivered crate snapshots onto a base crate, build and score.

  integrate.py --name NAME --base-src <crate> --part <label>=<crate snapshot dir> [--part ...]
               [--base-of <label>=<crate it was derived from>]
               [--no-build | --fresh-control --expect-base-sha256 <digest>]

Each part is turned into a patch against the crate it was derived from (default: --base-src),
then applied in order. Empty-file transitions use Git patch metadata; ordinary text
changes retain `patch -p2 --forward`. File and directory changes are checked
together before changing the composed tree. Directory changes are applied after
each file patch; a removal that still holds composed files is reported as retained.
Rejects are reported and the part is skipped (the composition continues).
Historical mode builds the composed crate and scores against the checked-in
baseline. Explicit fresh-control mode instead builds the admitted base and
composition in isolated cold workspaces, scores both against private copies of
the same captured evidence, and refuses any lost membership.
A build runs arbitrary build-script code, so the composed source, the scoring
baseline and the scorer are rechecked after the build; a build that changes
any of them is refused a score.
Output: SC/integ/<NAME>/{src, parts/<label>.patch, rejects/, report.json}
Fresh mode additionally retains fresh-control/{receipt.json, scoring inputs,
build artifacts, score reports}; its receipt is the authoritative qualification.
Names must be fresh; an earlier result is never overwritten.
Part labels must be unique ignoring case so their retained patch names remain
distinct on case-insensitive filesystems. Labels and composition names exclude
trailing dots and reserved Windows device names. --base-of labels match the
declared --part spelling exactly.
"""
import argparse, ast, errno, hashlib, json, os, secrets, shutil, subprocess, sys, re, tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
SC = H.parent
sys.path.insert(0, str(H))
from treediff import reject_source_link
from source_inputs import snapshot, assert_unchanged


def git_environment():
    # -C/cwd does not override repository/index paths exported by Git hooks or
    # another worktree. Git operations must belong to the owned composition.
    return {key: value for key, value in os.environ.items()
            if not key.upper().startswith('GIT_')}


def build_source(*args, **kwargs):
    # File-only composition does not need the builder's POSIX locking support.
    import fastbuild
    return fastbuild.build(*args, **kwargs)


def run_fresh_control(*args, **kwargs):
    # Preserve --no-build and historical-mode portability: fresh_control imports
    # the compiler coordinator and is loaded only for the explicit paired mode.
    import types
    path = H / 'fresh_control_inputs.py'
    raw = path.read_bytes()
    admission = types.ModuleType('_fresh_control_admission')
    admission.__file__ = str(path)
    admission.__dict__['_ADMITTED_SOURCE_BYTES'] = raw
    exec(compile(raw, str(path), 'exec', dont_inherit=True), admission.__dict__)
    return admission.load_context().load('fresh_control').run_pair(*args, **kwargs)


def publish_report(path, report):
    """Atomically replace this run's report without exposing partial JSON."""
    payload = json.dumps(report, indent=1, ensure_ascii=False) + '\n'
    for _ in range(100):
        temporary = path.parent / f'.report-{os.getpid()}-{secrets.token_hex(8)}'
        try:
            stream = temporary.open('x', encoding='utf-8', newline='\n')
        except FileExistsError:
            continue
        break
    else:
        raise FileExistsError('could not create integration report staging file')
    metadata = os.fstat(stream.fileno())
    identity = metadata.st_dev, metadata.st_ino
    try:
        with stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                current = temporary.lstat()
            except FileNotFoundError:
                pass
            else:
                if (current.st_dev, current.st_ino) == identity:
                    temporary.unlink()


def scoring_subprocess(command, **kwargs):
    """Run the scorer with no bytecode cache beside the harness to read.

    The build runs arbitrary build-script code before the scorer starts, and a
    __pycache__ entry whose header matches the source's mtime and size is
    executed in place of that source. -B and -I stop imports from writing
    bytecode; they do not stop them from reading it. Give the child an empty
    cache directory of its own so the modules it imports are compiled from the
    sources on disk.
    """
    with tempfile.TemporaryDirectory(prefix='pump-score-cache-') as cache:
        env = {**os.environ, 'PYTHONPYCACHEPREFIX': cache, 'PYTHONDONTWRITEBYTECODE': '1'}
        return subprocess.run(command, env=env, **kwargs)


def bound_capture(path):
    """Return the ELF score.py scores against for this checkout's link form.

    A native checkout stores base/original.so as a symlink, which read_bytes()
    already follows; a core.symlinks=false checkout stores the link payload as
    a regular file, and original_input resolves it to the real capture. A
    synthetic harness may ship integrate.py alone, and then the path is bound
    as given.
    """
    try:
        from original_input import resolve_original
    except ImportError:
        return path
    return resolve_original(path)


def bound_scoring_inputs(src, baseline):
    """Digest the composed source, scoring baseline and the scorer's inputs.

    A crate build runs arbitrary build-script code, so the build may rewrite
    the composed tree it is scored from, the baseline it is scored against,
    the scorer itself, or anything the scorer reads or imports;
    build_score_pair rechecks its bound inputs after the paired build for the
    same reason. Content hashes (not mtimes) bind the tree, so a build that
    only touches timestamps is not a change.

    score.py reads the reference ELF and the window inventory through BASE
    (resolve_original(BASE/'original.so') and BASE/'functions.tsv') and loads
    the modules beside it, so those are bound alongside the scorer.
    """
    def sha_file(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    tree = {}
    for path in sorted(src.rglob('*')):
        relative = path.relative_to(src).as_posix()
        if path.is_symlink():
            tree[relative] = 'symlink:' + os.readlink(path)
        elif path.is_file():
            tree[relative] = sha_file(path)
    scorer = H / 'score.py'
    support = {path.name: sha_file(path) for path in sorted(H.glob('*.py'))}
    base = SC / 'base'
    reference = {}
    for name in ('original.so', 'functions.tsv'):
        path = base / name
        try:
            if name == 'original.so':
                # score.py scores against the resolved capture, not the link.
                path = bound_capture(path)
            reference[name] = sha_file(path) if path.is_file() else None
        except OSError:
            # A synthetic harness may omit the capture; binding absence still
            # detects a reference file created during the build.
            reference[name] = None
    # Synthetic/minimal harnesses may omit the scorer and stub its invocation.
    # Binding absence still detects a scorer created during the build.
    return {'source': tree, 'baseline': sha_file(baseline), 'reference': reference,
            'support': support, 'scorer': support.get(scorer.name)}


def crate_ignore(root: Path, *patterns):
    """Skip Git metadata, the crate-root build directory, and `patterns` anywhere.

    Nested target directories and a regular file named target are source inputs.
    """
    root = Path(root)
    by_name = shutil.ignore_patterns('.git', *patterns)

    def ignore(directory, names):
        ignored = set(by_name(directory, names))
        if Path(directory) == root and 'target' in names and (root / 'target').is_dir():
            ignored.add('target')
        return ignored
    return ignore


def composition_directories(root: Path):
    """Directories a composition copy of `root` contains, after crate_ignore."""
    root = Path(root)
    ignore = crate_ignore(root, '*.rej', '.DS_Store')
    result = set()
    def traversal_error(error):
        raise error
    for directory, dirs, files in os.walk(root, onerror=traversal_error):
        skipped = set(ignore(directory, dirs + files))
        dirs[:] = sorted(d for d in dirs if d not in skipped)
        if Path(directory) != root:
            result.add(Path(directory).relative_to(root).as_posix())
    return result


def directory_delta(derived_from: Path, part: Path):
    before, after = composition_directories(derived_from), composition_directories(part)
    return sorted(after - before), sorted(before - after)


def apply_directory_delta(src: Path, added, removed):
    """Apply a part's directory delta; keep a removal that still holds composed files."""
    for name in added:
        (src / name).mkdir(parents=True, exist_ok=True)
    retained = []
    for name in sorted(removed, key=lambda value: value.count('/'), reverse=True):
        try:
            (src / name).rmdir()
        except (FileNotFoundError, NotADirectoryError):
            # A file patch may already have replaced this directory with a file.
            pass
        except OSError as error:
            if error.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                raise
            retained.append(name)
    return retained


def make_patch(base: Path, part: Path, out: Path, tmp: Path):
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / 'a').mkdir(parents=True); (tmp / 'b').mkdir(parents=True)
    patterns = ('*.rej', '.DS_Store')
    shutil.copytree(base, tmp / 'a/pump', ignore=crate_ignore(base, *patterns))
    shutil.copytree(part, tmp / 'b/pump', ignore=crate_ignore(part, *patterns))
    trees = [{p.relative_to(root): p.stat().st_size == 0
              for p in root.rglob('*') if p.is_file()}
             for root in (tmp / 'a/pump', tmp / 'b/pump')]
    # diff -N equates absent and empty files, while patch -E removes files
    # intentionally emptied by a part. Git records those existence changes.
    empty_change = any(trees[0].get(name, False) != trees[1].get(name, False)
                       for name in trees[0].keys() | trees[1].keys())
    # Source receipts bind executable flags too. Text diff cannot retain them.
    modes = [{p.relative_to(root): bool(p.stat().st_mode & 0o111)
              for p in root.rglob('*') if p.is_file()}
             for root in (tmp / 'a/pump', tmp / 'b/pump')]
    mode_change = any(modes[0].get(name, False) != modes[1].get(name, False)
                      for name in modes[0].keys() | modes[1].keys())
    directories = [{p.relative_to(root) for p in root.rglob('*') if p.is_dir()}
                   for root in (tmp / 'a/pump', tmp / 'b/pump')]
    type_change = bool(trees[0].keys() & directories[1] or trees[1].keys() & directories[0])
    if mode_change:
        # Git represents executable files using the owner bit. Source identity
        # considers any execute bit, including group/other-only helpers.
        for root, flags in zip((tmp / 'a/pump', tmp / 'b/pump'), modes):
            for name, executable in flags.items():
                path = root / name
                mode = path.stat().st_mode
                path.chmod(mode | 0o100 if executable else mode & ~0o100)
    git_diff = ['git', '-c', 'core.autocrlf=false', 'diff', '--no-index', '--binary',
                '--no-color', '--no-ext-diff', '--no-textconv', '--no-renames', '--src-prefix=',
                '--dst-prefix=', '--', 'a/pump', 'b/pump']

    def run_diff(command):
        # Binary-file diagnostics are parsed below; do not inherit a translated locale.
        environment = git_environment() if command[0] == 'git' else dict(os.environ)
        result = subprocess.run(command, cwd=tmp, capture_output=True,
                                env=dict(environment, LC_ALL='C'))
        if result.returncode not in (0, 1):
            raise subprocess.CalledProcessError(result.returncode, result.args,
                                                output=result.stdout, stderr=result.stderr)
        return result

    d = run_diff(git_diff if empty_change or mode_change or type_change else ['diff', '-ruN', 'a/pump', 'b/pump'])
    # diff -r only names binary changes, and patch skips that line without an error.
    if any(line.startswith(b'Binary files ') for line in d.stdout.splitlines()):
        d = run_diff(git_diff)
    out.write_bytes(d.stdout)
    # Decode only for report metadata; patch must receive the original diff bytes.
    return d.stdout.decode('utf-8', errors='surrogateescape')


def git_patch_command(source):
    # git apply invoked from a repository subdirectory silently filters paths
    # outside that prefix. Anchor at the root and prepend the owned output tree.
    found = subprocess.run(['git', '-C', str(source), 'rev-parse', '--show-toplevel'],
                           capture_output=True, env=git_environment())
    root = Path(os.fsdecode(found.stdout).rstrip('\r\n')).resolve() if found.returncode == 0 else source.resolve()
    directory = source.resolve().relative_to(root).as_posix()
    command = ['git', '-c', 'core.autocrlf=false', 'apply', '--no-index',
               '--whitespace=nowarn', '-p2']
    if directory != '.':
        command.append('--directory=' + directory)
    return command, root, directory


def git_patched_files(command, root, directory, patch):
    # NUL-delimited metadata covers empty files and arbitrary quoted filenames.
    result = subprocess.run(command + ['--numstat', '-z', str(patch)], cwd=root,
                            capture_output=True, check=True, env=git_environment())
    names = [entry.split(b'\t', 2)[2].decode('utf-8', errors='surrogateescape')
             for entry in result.stdout.split(b'\0') if entry]
    return sorted(Path(name).relative_to(directory).as_posix() for name in names)


def patched_files(text: str):
    files = set()
    in_headers = False
    for line in text.split('\n'):
        if line.startswith('diff '):
            in_headers = True
        elif line.startswith('@@'):
            in_headers = False
        if not in_headers or not line.startswith('+++ '):
            continue
        name = line[4:].split('\t', 1)[0]
        if name.startswith('"') and name.endswith('"'):
            # GNU diff C-quotes paths, including octal UTF-8 bytes. Decode a
            # bytes literal so those escapes round-trip to the original path.
            literal = name.encode('utf-8', errors='surrogateescape').decode('ascii', errors='backslashreplace')
            name = ast.literal_eval('b' + literal).decode('utf-8', errors='surrogateescape')
        if name.startswith('b/pump/'):
            files.add(name[len('b/pump/'):])
    return sorted(files)


def apply_file_patch(source, patch, text, patch_command):
    if text.startswith('diff --git '):
        command, root, directory = git_patch_command(source)
        subprocess.run(command + [str(patch)], cwd=root, check=True,
                       capture_output=True, env=git_environment())
        return git_patched_files(command, root, directory, patch)
    subprocess.run(patch_command + ['-s', '-p2', '--forward', '-E', '-d', str(source),
                                   '-i', str(patch)], check=True, capture_output=True)
    return patched_files(text)


def reject_source_tree_links(root: Path):
    """Reject links before copytree can follow them into a composition."""
    reject_source_link(root)
    if not root.is_dir():
        return  # Preserve the existing missing/not-a-crate diagnostics.
    # Check entries as rglob yields them. Building an eager list first could
    # already traverse a Windows directory junction before it is inspected.
    for path in root.rglob('*'):
        reject_source_link(path)


def preflight(name, base, parts, overrides):
    """Validate the complete composition before touching its output or snapshots."""
    def label(value):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value) or value in ('.', '..'):
            raise ValueError(f'invalid composition name or label: {value!r}')
        reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {
            f'{prefix}{number}' for prefix in ('COM', 'LPT') for number in range(1, 10)
        }
        if value.endswith('.') or value.split('.', 1)[0].upper() in reserved:
            raise ValueError(f'nonportable composition name or label: {value!r}')
        return value

    def selections(values, kind):
        result = {}
        folded = set()
        for value in values:
            if '=' not in value:
                raise ValueError(f'{kind} must be LABEL=PATH')
            key, path = value.split('=', 1)
            label(key)
            if key.casefold() in folded or not path:
                raise ValueError(f'duplicate label or empty path in {kind}: {key}')
            folded.add(key.casefold())
            result[key] = Path(path)
        return result

    label(name)
    selected = selections(parts, '--part')
    bases = selections(overrides, '--base-of')
    unknown = bases.keys() - selected.keys()
    if unknown:
        raise ValueError('base overrides have no matching part: ' + ', '.join(sorted(unknown)))
    output_path = SC / 'integ' / name
    if output_path.exists() or output_path.is_symlink():
        raise ValueError('output already exists; choose a new --name to preserve the earlier result')
    for source in {Path(base), *selected.values(), *bases.values()}:
        reject_source_tree_links(source)
    out = output_path.resolve()
    base = Path(base).resolve()
    selected = {key: path.resolve() for key, path in selected.items()}
    bases = {key: path.resolve() for key, path in bases.items()}
    scratch_paths = [(SC / 'integ' / '.tmp' / name / key).resolve()
                     for key in selected]
    for source in {base, *selected.values(), *bases.values()}:
        if source == out or source in out.parents or out in source.parents:
            raise ValueError(f'source overlaps composition output: {source}')
        for scratch in scratch_paths:
            if source == scratch or source in scratch.parents or scratch in source.parents:
                raise ValueError(f'source overlaps composition scratch: {source}')
        if not source.is_dir() or not (source / 'src').is_dir():
            raise ValueError(f'source is not a crate directory with src/: {source}')
        for required in ('Cargo.toml', 'Cargo.lock'):
            if not (source / required).is_file():
                raise ValueError(f'source is missing {required}: {source}')
    return out, base, [(key, path, bases.get(key, base)) for key, path in selected.items()]


def apply_part(src, pf, text, patch_command, diagnostic):
    """Only exit 1 from a dry run is a skippable content conflict."""
    try:
        git_format = text.startswith('diff --git ')
        if git_format:
            command, root, directory = git_patch_command(src)
            dry_command = command + ['--check', str(pf)]
            apply_command = command + [str(pf)]
        else:
            root = None
            common = patch_command + ['-p2', '--forward', '-E', '-d', str(src), '-i', str(pf)]
            dry_command, apply_command = common + ['--dry-run'], common
        for phase, argv in [('check', dry_command), ('apply', apply_command)]:
            # Patch diagnostics can contain UTF-8 filenames even under LC_ALL=C.
            # They are display text only; patch input stays byte-preserving.
            result = subprocess.run(argv, cwd=root, capture_output=True,
                                    encoding='utf-8', errors='replace',
                                    env=git_environment() if git_format else None)
            if result.returncode:
                detail = result.stdout + result.stderr
                diagnostic.write_text(detail, encoding='utf-8', newline='\n')
                return {'status': 'conflict' if phase == 'check' and result.returncode == 1 else 'error',
                        'phase': phase, 'returncode': result.returncode, 'detail': detail[-1500:]}
        files = git_patched_files(command, root, directory, pf) if git_format else patched_files(text)
        return {'status': 'applied', 'files': files}
    except (OSError, subprocess.CalledProcessError) as error:
        detail = str(error)
        for value in (getattr(error, 'stdout', None), getattr(error, 'stderr', None)):
            if value:
                detail += '\n' + (value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value)
        diagnostic.write_text(detail, encoding='utf-8', newline='\n')
        return {'status': 'error', 'detail': detail[-1500:]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--name', required=True)
    ap.add_argument('--base-src', type=Path, required=True)
    ap.add_argument('--part', action='append', default=[])
    ap.add_argument('--base-of', action='append', default=[])
    ap.add_argument('--no-build', action='store_true')
    ap.add_argument('--fresh-control', action='store_true',
                    help='build and score admitted base plus composition; reject every fresh loss')
    ap.add_argument('--expect-base-sha256',
                    help='required source_inputs.py digest for --fresh-control base admission')
    ap.add_argument('--sdk', type=Path,
                    default=Path.home() / '.cache/solana/v1.44/platform-tools')
    ap.add_argument('--hybrid', type=Path,
                    default=Path(os.environ.get('PUMP_RECON_HOME', str(Path.home() / '.cache/pumpfun-reconstruction'))) / 'toolchains/hybrid144')
    ap.add_argument('--timeout', type=float, help='compiler deadline in seconds')
    a = ap.parse_args()
    # GNU patch in POSIX mode cannot locate a file that diff -N records as new,
    # which would report every part adding a file as a content conflict.
    os.environ.pop('POSIXLY_CORRECT', None)
    if a.timeout is not None:
        from build_process import validate_timeout
        try:
            validate_timeout(a.timeout)
        except ValueError as error:
            ap.error(str(error))
    if a.fresh_control and a.no_build:
        ap.error('--fresh-control cannot be combined with --no-build')
    if a.fresh_control:
        if not a.expect_base_sha256 or not re.fullmatch(r'[0-9a-f]{64}', a.expect_base_sha256):
            ap.error('--fresh-control requires --expect-base-sha256 as 64 lowercase hex digits')
    elif a.expect_base_sha256:
        ap.error('--expect-base-sha256 is only valid with --fresh-control')
    baseline = SC / 'pump-main/baseline/score.json'
    if not a.no_build and not a.fresh_control and not baseline.is_file():
        raise FileNotFoundError(f'Required scoring baseline is missing: {baseline}')
    try:
        out, base, parts = preflight(a.name, a.base_src, a.part, a.base_of)
    except (ValueError, OSError) as error:
        ap.error(str(error))
    if a.fresh_control:
        try:
            admitted_base = snapshot(base)
        except (OSError, ValueError) as error:
            ap.error(str(error))
        if admitted_base['sha256'] != a.expect_base_sha256:
            ap.error('fresh base source digest differs from --expect-base-sha256')
    (out / 'parts').mkdir(parents=True); (out / 'rejects').mkdir()
    report = {'name': a.name, 'base': str(a.base_src),
              'mode': 'fresh_control' if a.fresh_control else ('compose_only' if a.no_build else 'historical_baseline'),
              'parts': []}
    exit_code = 0
    try:
        sources = sorted({base, *(path for _, path, _ in parts), *(derived for _, _, derived in parts)}, key=str)
        before = {path: snapshot(path) for path in sources}
        before_dirs = {path: composition_directories(path) for path in sources}
        owned = {}
        for index, path in enumerate(sources):
            copied = out / 'inputs' / str(index)
            shutil.copytree(path, copied, ignore=crate_ignore(path))
            assert_unchanged(path, before[path])
            assert_unchanged(copied, before[path])
            if composition_directories(copied) != before_dirs[path]:
                raise ValueError('source directories changed during staging')
            owned[path] = copied
        def validate_inputs():
            for path in sources:
                assert_unchanged(path, before[path])
                assert_unchanged(owned[path], before[path])
                if (composition_directories(path) != before_dirs[path]
                        or composition_directories(owned[path]) != before_dirs[path]):
                    raise ValueError('source directories changed during staging')
        report['sources'] = {str(path): value | {'directories': sorted(before_dirs[path])}
                             for path, value in before.items()}
        validate_inputs()
        base = owned[base]
        parts = [(label, owned[path], owned[derived]) for label, path, derived in parts]
        shutil.copytree(base, out / 'src', ignore=crate_ignore(base))
        src = out / 'src'
        # GNU patch on Windows otherwise strips CR bytes from patch/source input.
        patch_command = ['patch', '-V', 'none'] + (['--binary'] if sys.platform == 'win32' else [])
        for label, path, derived_from in parts:
            pf = out / 'parts' / f'{label}.patch'
            text = make_patch(derived_from, Path(path), pf, SC / 'integ' / '.tmp' / a.name / label)
            added, removed = directory_delta(derived_from, Path(path))
            if not text.strip() and not added and not removed:
                report['parts'].append({'label': label, 'status': 'empty'}); continue
            # A part is checked in a private tree, including its directory delta.
            # Neither conflicts nor patch-tool errors may partly modify src.
            prospective = SC / 'integ' / '.tmp' / a.name / label / 'prospective'
            shutil.copytree(src, prospective)
            # Both patch tools prune a directory when its last file goes.
            kept = composition_directories(prospective) & composition_directories(Path(path))
            diagnostic = out / 'rejects' / f'{label}.txt'
            result = (apply_part(prospective, pf, text, patch_command, diagnostic)
                      if text.strip() else {'status': 'applied', 'files': []})
            if result['status'] == 'applied':
                try:
                    retained = apply_directory_delta(prospective, sorted({*added, *kept}), removed)
                except (FileExistsError, NotADirectoryError) as error:
                    detail = 'directory composition conflict: ' + str(error)
                    diagnostic.write_text(detail, encoding='utf-8', newline='\n')
                    result = {'status': 'conflict', 'detail': detail}
                else:
                    if added or removed:
                        result['directories'] = {key: value for key, value in
                            (('added', added), ('removed', removed), ('retained', retained)) if value}
                    shutil.rmtree(src)
                    shutil.copytree(prospective, src)
            report['parts'].append({'label': label, **result})
            if result['status'] == 'error':
                exit_code = 1
                break
        validate_inputs()
        if a.fresh_control:
            rejected = [part for part in report['parts'] if part['status'] not in ('applied', 'empty')]
            if exit_code or rejected:
                report['qualification'] = {
                    'accepted': False,
                    'rejection_reasons': ['part_application_error' if exit_code else 'part_not_applied'],
                    'rejected_parts': [{'label': part['label'], 'status': part['status']} for part in rejected],
                }
                exit_code = 1
            else:
                fresh = run_fresh_control(base, src, out / 'fresh-control',
                                          sdk=a.sdk.resolve(), hybrid=a.hybrid.resolve(), timeout=a.timeout)
                report['fresh_control'] = fresh
                report['qualification'] = {
                    **fresh['qualification'],
                    'required_parts': [part['label'] for part in report['parts']],
                    'applied_parts': [part['label'] for part in report['parts']
                                      if part['status'] == 'applied'],
                    'empty_parts': [part['label'] for part in report['parts']
                                    if part['status'] == 'empty'],
                }
                if not report['qualification']['accepted']:
                    exit_code = 1
        elif not a.no_build and not exit_code:
            build_options = {'timeout': a.timeout} if a.timeout is not None else {}
            bound = bound_scoring_inputs(src, baseline)
            res = build_source(src, out / 'work', out / 'build', quiet=True, **build_options)
            report['build'] = res
            if res['ok'] and bound_scoring_inputs(src, baseline) != bound:
                report['score_error'] = {'error': 'composed source, scoring baseline or scorer changed during build; refusing to score'}
                exit_code = 1
            elif res['ok']:
                s = scoring_subprocess([sys.executable, str(H / 'score.py'), str(out / 'build/unstripped.so'),
                                   '--expect-sha256', res['unstripped_sha256'],
                                   '--baseline', str(baseline),
                                   '--json', str(out / 'score.json'), '--quiet'],
                                   capture_output=True, text=True)
                if s.returncode:
                    report['score_error'] = {'returncode': s.returncode, 'stdout': s.stdout, 'stderr': s.stderr}
                    exit_code = 1
                else:
                    try:
                        report['score'] = json.loads(s.stdout)
                    except json.JSONDecodeError:
                        report['score_error'] = {'returncode': s.returncode, 'stdout': s.stdout,
                                                 'stderr': s.stderr, 'error': 'scorer returned invalid JSON'}
                        exit_code = 1
            else:
                exit_code = 1
        validate_inputs()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        report['error'] = str(error)
        exit_code = 1
    publish_report(out / 'report.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'parts'} | {'parts': [{k: p[k] for k in ('label', 'status')} for p in report['parts']]}, indent=1))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
