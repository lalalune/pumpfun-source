"""Donation Relay's measured native input profile and path-only replay helpers.

No network acquisition, credential discovery, compiler fallback or input substitution.
"""
from pathlib import Path, PurePosixPath
import gzip
import hashlib
import io
import json
import os
import shutil
import signal
import stat
import struct
import subprocess
import tarfile
import time

PACKAGE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def load(name):
    return json.loads((PACKAGE / name).read_text())


def write_new(path, value):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def check_assets():
    for row in load('ARTIFACTS.json')['artifacts']:
        p = PACKAGE / row['path']
        require(p.stat().st_size == row['bytes'] and digest(p) == row['sha256'],
                'packet asset mismatch: ' + row['path'])


def safe_name(name):
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe archive path: ' + name)
    return p.as_posix()


def tar_members(path):
    result = {}
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            name = safe_name(member.name)
            require(member.isfile() and name not in result, 'unexpected/duplicate archive member: ' + name)
            result[name] = archive.extractfile(member).read()
    return result


def check_source(source, modes=True):
    source = Path(source)
    rows = load('source-inputs.json')['files']
    require({p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
            == {r['path'] for r in rows}, 'source file inventory mismatch')
    for row in rows:
        p = source / row['path']
        require(p.is_file() and not p.is_symlink() and digest(p) == row['sha256'],
                'source hash/type mismatch: ' + row['path'])
        if modes:
            require(stat.S_IMODE(p.stat().st_mode) == int(row['mode'], 8) & 0o7777,
                    'source mode mismatch: ' + row['path'])


def check_config(config):
    for name, wanted in load('recipe.json')['configInputs'].items():
        require(digest(Path(config) / name) == wanted, 'configuration hash mismatch: ' + name)
    require(os.access(Path(config) / 'linker-wrapper.sh', os.X_OK), 'linker wrapper is not executable')


def check_sdk(sdk):
    sdk = Path(sdk)
    spec = load('sdk-inputs.json')
    missing = [row['path'] for row in spec['files'] if not (sdk / row['path']).exists()]
    require(not missing, 'missing SDK members: ' + ', '.join(missing))
    expected = {r['path'] for r in spec['files']}
    actual = {p.relative_to(sdk).as_posix() for p in sdk.rglob('*') if p.is_file() or p.is_symlink()}
    require(actual == expected, 'SDK file inventory differs from the measured subset')
    for row in spec['files']:
        p = sdk / row['path']
        if row['type'] == 'symlink':
            require(p.is_symlink() and os.readlink(p) == row['linkTarget']
                    and p.resolve().is_relative_to(sdk.resolve()), 'SDK alias mismatch: ' + row['path'])
        else:
            require(p.is_file() and not p.is_symlink() and p.stat().st_size == row['size']
                    and digest(p) == row['sha256'], 'SDK content mismatch: ' + row['path'])
            require(stat.S_IMODE(p.stat().st_mode) == int(row['mode'], 8) & 0o7777,
                    'SDK mode mismatch: ' + row['path'])
    for row in spec['directories']:
        p = sdk / row['path']
        require(p.is_dir() and not p.is_symlink()
                and stat.S_IMODE(p.stat().st_mode) == int(row['mode'], 8) & 0o7777,
                'SDK directory mismatch: ' + row['path'])


def check_registry(registry):
    registry = Path(registry)
    spec = load('registry-inputs.json')
    namespace = spec['indexDirectory']
    vector = json.loads(gzip.decompress((PACKAGE / 'registry-source-vector.json.gz').read_bytes()))
    require(len(vector) == 7968, 'registry vector count mismatch')
    by_package = {}
    for row in vector:
        by_package.setdefault(row['package'], []).append(row)
        p = registry / 'src' / namespace / row['package'] / row['path']
        require(p.is_file() and not p.is_symlink() and p.stat().st_size == row['bytes']
                and digest(p) == row['sha256'], 'registry source mismatch: ' + row['package'] + '/' + row['path'])
        require(stat.S_IMODE(p.stat().st_mode) == int(row['mode'], 8) & 0o7777,
                'registry source mode mismatch: ' + row['package'] + '/' + row['path'])
    for row in spec['packages']:
        name = row['name']
        archive = registry / 'cache' / namespace / (name + '.crate')
        require(digest(archive) == row['checksum'], 'locked archive checksum mismatch: ' + name)
        src = registry / 'src' / namespace / name
        require(digest(src / '.cargo-checksum.json') == row['generatedChecksumSHA256'],
                'Cargo checksum metadata differs from measured profile: ' + name)
        require(digest(src / '.cargo-ok') == row['generatedMarkerSHA256'], 'Cargo marker mismatch: ' + name)
        expected = {r['path'] for r in by_package[name]} | {'.cargo-checksum.json', '.cargo-ok'}
        require({p.relative_to(src).as_posix() for p in src.rglob('*') if p.is_file()} == expected,
                'registry package file inventory mismatch: ' + name)
    index = registry / 'index' / namespace
    for row in spec['publicSparseIndex']['retainedFiles']:
        require(digest(index / row['path']) == row['sha256'], 'public index metadata mismatch: ' + row['path'])


def check_host():
    host = json.loads(gzip.decompress((PACKAGE / 'host-inputs.json.gz').read_bytes()))
    groups = [host['executablesAndRuntimeClosure'].values(), host['seedAliases'],
              host['linkerCrtAndStaticInputs'], host['conservativeHostHeaderInputs'],
              load('sdk-inputs.json')['nativeRuntimeLibraries'].values()]
    for rows in groups:
        for row in rows:
            require(digest(Path(row['path'])) == row['sha256'], 'unqualified host input: ' + row['path'])
    aliases = load('host-aliases.json')
    for row in aliases['aliases']:
        p = Path(row['logicalPath'])
        require(p.is_symlink() and os.readlink(p) == row['linkTarget']
                and digest(p) == row['resolvedSHA256'], 'host compiler alias mismatch: ' + str(p))
    require(digest(Path(aliases['loaderCache']['path'])) == aliases['loaderCache']['sha256'],
            'native loader cache differs from measured host')


def command(work, sdk, registry, tail=None):
    """Same ACTUAL attempt2 argv, with only seven physical mount roots replaced."""
    work, sdk, registry = Path(work).resolve(), Path(sdk).resolve(), Path(registry).resolve()
    recipe = load('recipe.json')
    argv = ['bwrap', '--unshare-user', '--unshare-net', '--die-with-parent', '--tmpfs', '/',
            '--proc', '/proc', '--dev', '/dev', '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
            '--ro-bind', '/lib64', '/lib64', '--symlink', 'usr/bin', '/bin', '--symlink', 'usr/sbin', '/sbin',
            '--dir', '/etc', '--ro-bind', '/etc/ld.so.cache', '/etc/ld.so.cache',
            '--ro-bind', str(work / 'host-aliases'), '/etc/alternatives',
            '--ro-bind', str(work / 'source'), '/source', '--ro-bind', str(work / 'config'), '/config',
            '--ro-bind', str(sdk), '/sdk', '--tmpfs', '/cargo', '--ro-bind', str(registry), '/cargo/registry',
            '--bind', str(work / 'target'), '/target', '--bind', str(work / 'output'), '/output',
            '--tmpfs', '/tmp', '--chdir', '/source', '--', '/usr/bin/env', '-i']
    return argv + [k + '=' + v for k, v in recipe['canonicalEnvironment'].items()] + (
        recipe['canonicalCargoArgv'] if tail is None else list(tail))


def stage(repo, sdk, registry, work):
    """Validate all inputs before creating a new work area. Never executes an SDK tool."""
    check_assets()
    repo, sdk, registry, work = (Path(p).resolve() for p in [repo, sdk, registry, work])
    require(not work.exists(), 'work path already exists; preserve it and select a new path')
    source = (repo / 'programs/donation-relay').resolve()
    for root in [source, sdk, registry, PACKAGE.resolve()]:
        require(not work.is_relative_to(root) and not root.is_relative_to(work),
                'work path overlaps an authenticated input root: ' + str(root))
    # Incoming checkout permissions can reflect umask. Owned staged copies below
    # receive the exact measured Git modes; their contents/types are unchanged.
    check_source(source, modes=False); check_config(PACKAGE / 'layout'); check_sdk(sdk); check_registry(registry); check_host()
    work.mkdir(parents=True, exist_ok=False)
    for row in load('source-inputs.json')['files']:
        p = work / 'source' / row['path']; p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / row['path'], p); p.chmod(int(row['mode'], 8) & 0o7777)
    shutil.copytree(PACKAGE / 'layout', work / 'config')
    check_source(work / 'source')
    (work / 'host-aliases').mkdir()
    for row in load('host-aliases.json')['aliases']:
        (work / 'host-aliases' / Path(row['logicalPath']).name).symlink_to(row['linkTarget'])
    plan = {'scope': 'Public path-only replay plan; NOT a new cold measurement', 'sdk': str(sdk),
            'registry': str(registry), 'work': str(work), 'sourceFiles': 60,
            'argv': command(work, sdk, registry), 'sourceCompilations': 0,
            'recipeSHA256': digest(PACKAGE / 'recipe.json')}
    write_new(work / 'plan.json', plan)
    return plan


def validate_staged(work):
    work = Path(work).resolve(); plan = json.loads((work / 'plan.json').read_text())
    check_assets(); check_source(work / 'source'); check_config(work / 'config')
    check_sdk(Path(plan['sdk'])); check_registry(Path(plan['registry'])); check_host()
    require(plan['work'] == str(work), 'staged work path was moved; restage at the desired path')
    require(plan['recipeSHA256'] == digest(PACKAGE / 'recipe.json'), 'recipe changed after staging')
    require(plan['argv'] == command(work, plan['sdk'], plan['registry']), 'plan argv differs from canonical recipe')
    for row in load('host-aliases.json')['aliases']:
        p = work / 'host-aliases' / Path(row['logicalPath']).name
        require(p.is_symlink() and os.readlink(p) == row['linkTarget'], 'staged host alias mismatch')
    return plan


def free_bytes(path):
    s = os.statvfs(path)
    return s.f_bavail * s.f_frsize


def monitored(argv, destination, name, timeout, floor):
    """Same floor/time/process-group policy as the measured controller."""
    start = time.monotonic(); reason = None; minimum = free_bytes(destination)
    with (destination / (name + '.log')).open('xb') as log, (destination / (name + '-resources.jsonl')).open('x') as samples:
        p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write_new(destination / (name + '-process.json'), {'pid': p.pid, 'argv': argv})
        last = -1
        while p.poll() is None:
            elapsed = time.monotonic() - start; available = free_bytes(destination); minimum = min(minimum, available)
            if int(elapsed) != last:
                samples.write(json.dumps({'seconds': elapsed, 'freeBytes': available}) + '\n'); samples.flush(); last = int(elapsed)
            if available < floor: reason = 'HOST_DISK_FLOOR_128_MIB'; break
            if elapsed > timeout: reason = 'TIMEOUT'; break
            time.sleep(.1)
        if reason:
            try: os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try: os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait()
        else: p.wait()
        minimum = min(minimum, free_bytes(destination))
        if minimum < floor and reason is None: reason = 'HOST_DISK_FLOOR_128_MIB_AFTER_EXIT'
    group_left = False
    try: os.killpg(p.pid, 0); group_left = True
    except ProcessLookupError: pass
    if group_left:
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        reason = reason or 'OWNED_GROUP_REMAINED_AFTER_LEADER_EXIT'
    return {'returncode': p.returncode, 'seconds': time.monotonic() - start,
            'guardFired': reason, 'lowestFreeBytes': minimum, 'groupRemained': group_left}


def execute(work):
    work = Path(work).resolve(); plan = validate_staged(work); recipe = load('recipe.json')
    require(not (work / 'target').exists() and not (work / 'output').exists(),
            'fresh target/output required; existing/failed attempts are preserved')
    require(free_bytes(work) > recipe['floorBytes'], 'insufficient free space before launch')
    (work / 'target').mkdir(); (work / 'output').mkdir(); (work / 'output/home').mkdir()
    result = {'scope': 'Actual execution of the public path-only launcher; no automatic retries',
              'build': monitored(plan['argv'], work, 'build', recipe['timeoutSeconds'], recipe['floorBytes'])}
    write_new(work / 'result.json', result)
    validate_staged(work)
    if result['build']['returncode'] or result['build']['guardFired']:
        return result
    log = (work / 'build.log').read_bytes()
    require(log.count(b'--crate-name donation_relay_source_proposal ') == 1
            and log.count(b'--crate-name relay_error_model_reconstructed ') == 1,
            'expected one fresh compiler invocation for each local crate')
    output = work / 'output'
    shutil.copyfile(work / 'target/sbpf-solana-solana/release/donation_relay_source_proposal.so', output / 'symbols.so')
    result['strip'] = monitored(command(work, plan['sdk'], plan['registry'], recipe['stripArgv']),
                                work, 'strip', 60, recipe['floorBytes'])
    if result['strip']['returncode'] == 0 and result['strip']['guardFired'] is None:
        result['outputs'] = {n: {'bytes': (output / n).stat().st_size, 'sha256': digest(output / n)}
                             for n in recipe['expectedOutputs']}
        result['canonicalOutputHashesEqual'] = result['outputs'] == recipe['expectedOutputs']
    validate_staged(work)
    # Replace only this new launcher's own interim result, never a retained measurement.
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def extract_sdk(archive, out):
    check_assets(); archive, out = Path(archive), Path(out)
    spec = load('sdk-inputs.json')
    require(not out.exists(), 'SDK output already exists; preserve it')
    require(archive.stat().st_size == spec['archive']['bytes'] and digest(archive) == spec['archive']['sha256'],
            'SDK archive differs from the pinned measured archive')
    out.mkdir(parents=True, exist_ok=False)
    wanted = {r['path']: r for r in spec['files']}; seen = set()
    with tarfile.open(archive, 'r|bz2') as tar:
        for m in tar:
            name = safe_name(m.name)
            if name not in wanted: continue
            require(name not in seen, 'duplicate selected SDK member'); seen.add(name); row = wanted[name]
            if row['type'] == 'symlink':
                require(m.issym() and m.linkname == row['linkTarget'], 'SDK alias header mismatch'); continue
            require(m.isfile() and m.size == row['size'] and m.mode == int(row['mode'], 8), 'SDK member header mismatch: ' + name)
            p = out / name; p.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(m) as src, p.open('xb') as dst: shutil.copyfileobj(src, dst)
            p.chmod(int(row['mode'], 8) & 0o7777)
            require(digest(p) == row['sha256'], 'SDK extracted member mismatch: ' + name)
    require(seen == set(wanted), 'selected SDK members absent from archive')
    for row in spec['directories']:
        p = out / row['path']; p.mkdir(parents=True, exist_ok=True); p.chmod(int(row['mode'], 8) & 0o7777)
    for row in spec['files']:
        if row['type'] == 'symlink': (out / row['path']).symlink_to(row['linkTarget'])
    check_sdk(out)


def prepare_registry(archives, out):
    check_assets(); archives, out = Path(archives), Path(out); spec = load('registry-inputs.json')
    require(not out.exists(), 'registry output already exists; preserve it')
    for row in spec['packages']:
        require(digest(archives / (row['name'] + '.crate')) == row['checksum'], 'locked archive mismatch: ' + row['name'])
    out.mkdir(parents=True, exist_ok=False); namespace = spec['indexDirectory']
    for row in spec['packages']:
        name = row['name']; source = out / 'src' / namespace / name; source.mkdir(parents=True)
        cache = out / 'cache' / namespace / (name + '.crate'); cache.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archives / (name + '.crate'), cache); cache.chmod(0o644); files = {}
        with tarfile.open(cache, 'r:gz') as tar:
            for m in tar:
                path = PurePosixPath(safe_name(m.name)); require(path.parts[0] == name, 'crate root mismatch')
                rel = Path(*path.parts[1:]); p = source / rel
                require(p.resolve().is_relative_to(source.resolve()), 'crate path escape')
                if m.isdir(): p.mkdir(parents=True, exist_ok=True); p.chmod(m.mode & 0o7777); continue
                require(m.isfile() and rel.as_posix() not in files, 'unexpected/duplicate crate member')
                p.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as src, p.open('xb') as dst: shutil.copyfileobj(src, dst)
                p.chmod(m.mode & 0o7777); files[rel.as_posix()] = digest(p)
        (source / '.cargo-checksum.json').write_text(json.dumps({'files': files, 'package': row['checksum']}, separators=(',', ':')))
        (source / '.cargo-ok').write_bytes(b'{"v":1}')
    for name, data in tar_members(PACKAGE / 'registry-index.tar.gz').items():
        p = out / 'index' / namespace / name; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    check_registry(out)
