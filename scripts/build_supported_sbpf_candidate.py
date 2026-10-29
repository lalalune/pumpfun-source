#!/usr/bin/env python3
"""Proposed measured v1.53/v1.54 direct-Cargo adapter. --dry-run never invokes tools."""
import argparse, hashlib, importlib.util, json, ntpath, os, pathlib, platform, shutil, struct, subprocess, sys, tarfile, time, tomllib
sys.dont_write_bytecode = True  # Planning must not create utility __pycache__ files.
P = pathlib.Path(__file__).resolve().parent
PROGRAMS = ('pump', 'pump_amm', 'pump_fees', 'mayhem')
SUPPORTED = ('v1.53', 'v1.54')
PROFILE = {'panic': 'abort', 'overflow-checks': True, 'lto': False, 'codegen-units': 1}
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def parser():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--manifest', type=pathlib.Path, required=True)
    p.add_argument('--program', choices=PROGRAMS, required=True)
    p.add_argument('--artifact-name', required=True)
    p.add_argument('--tools-version', choices=SUPPORTED, required=True)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--extra-input', type=pathlib.Path, action='append', default=[])
    p.add_argument('--dry-run', action='store_true')
    return p


def repository():
    return next(p for p in P.parents if (p/'scripts/build_partial_candidate.py').is_file())


def validate_environment(env):
    names = {'RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC', 'RUSTDOC', 'RUSTC_WRAPPER',
             'RUSTC_WORKSPACE_WRAPPER', 'RUSTUP_TOOLCHAIN', 'RUSTC_BOOTSTRAP', 'RUST_TARGET_PATH',
             'CC', 'CXX', 'AR', 'RANLIB', 'LD', 'LINKER', 'OBJDUMP', 'OBJCOPY',
             'CFLAGS', 'CXXFLAGS', 'CPPFLAGS', 'LDFLAGS', 'RUSTDOCFLAGS', 'CARGO_INCREMENTAL',
             'LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES'}
    prefixes = ('CARGO_TARGET_', 'CARGO_PROFILE_', 'CARGO_BUILD_', 'CARGO_REGISTRY_', 'CARGO_REGISTRIES_',
                'RUSTC_', 'RUSTDOC_', 'CC_', 'CXX_', 'AR_', 'RANLIB_', 'CFLAGS_', 'CXXFLAGS_', 'CPPFLAGS_', 'LDFLAGS_')
    rejected = sorted(k for k in env if k in names or k.startswith(prefixes))
    if rejected:
        raise ValueError('Unrecorded recipe overrides are unsupported: '+', '.join(rejected))


def reject_configs(starts, cargo_source):
    directories = set()
    for start in starts:
        directories.update((start, *start.parents))
    configs = [d/n for d in directories for n in ('.cargo/config', '.cargo/config.toml') if (d/n).is_file()]
    configs += [cargo_source/n for n in ('config', 'config.toml') if (cargo_source/n).is_file()]
    if configs:
        raise ValueError('Unreviewed Cargo config: '+', '.join(map(str, sorted(set(configs)))))


def workspace_for(manifest, repo):
    for d in (manifest.parent, *manifest.parent.parents):
        f = d/'Cargo.toml'
        if f.is_file() and 'workspace' in tomllib.loads(f.read_text()):
            return d
        if d == repo:
            break
    raise ValueError('An explicit repository-local Cargo workspace is required')


def plan(a, repo, env, *, cache_root=None, policy_directory=None):
    """Pure filesystem reads; intentionally no Cargo metadata or compiler version query."""
    repo = repo.resolve(); manifest = a.manifest.resolve(); manifest.relative_to(repo)
    policy_dir = pathlib.Path(policy_directory or P/'supported_sbpf_policies')
    policy_path = policy_dir/(a.tools_version+'.json'); policy = json.loads(policy_path.read_text())
    if (platform.system(), platform.machine()) != (policy['measured_host']['system'], policy['measured_host']['machine']):
        raise ValueError('only the measured Darwin arm64 distribution is supported')
    if manifest.name != 'Cargo.toml' or not manifest.is_file():
        raise ValueError('manifest must be an existing repository-local Cargo.toml')
    output = a.output.resolve()
    if output.exists() or output.is_relative_to(manifest.parent):
        raise ValueError('output must be new and outside the source crate')
    if pathlib.Path(a.artifact_name).name != a.artifact_name or not a.artifact_name.endswith('.so') or '\\' in a.artifact_name:
        raise ValueError('artifact-name must be a .so basename')
    validate_environment(env)
    ws = workspace_for(manifest, repo)
    crate_toml = tomllib.loads(manifest.read_text()); workspace_toml = tomllib.loads((ws/'Cargo.toml').read_text())
    release = workspace_toml.get('profile', {}).get('release', {})
    if any(release.get(k) != v for k, v in PROFILE.items()) or release.get('opt-level', 3) != 3 or set(release)-set(PROFILE)-{'opt-level'}:
        raise ValueError('release profile differs from the measured recipe')
    if set(workspace_toml.get('profile', {})) != {'release'} or crate_toml.get('features', {}).get('default', []) != []:
        raise ValueError('unmeasured profile overrides or default features')
    lock = ws/'Cargo.lock'
    if not lock.is_file():
        raise ValueError('a frozen workspace Cargo.lock is required')
    if any(p.get('source') and p['source'] != 'registry+https://github.com/rust-lang/crates.io-index' for p in tomllib.loads(lock.read_text()).get('package', [])):
        raise ValueError('git/custom-registry dependency caches are outside this measured adapter recipe')
    cargo_source = pathlib.Path(env.get('CARGO_HOME', str(pathlib.Path.home()/'.cargo'))).resolve()
    if not (cargo_source/'registry').is_dir() or output.is_relative_to(cargo_source):
        raise ValueError('an existing offline registry cache outside output is required')
    reject_configs([manifest.parent, repo, output.parent], cargo_source)
    utility = repo/'scripts/build_source_manifest.py'
    if sha(utility) != policy['source_inventory_utility_sha256']:
        raise ValueError('source manifest utility changed; review its new input contract first')
    spec = importlib.util.spec_from_file_location('supported_builder_source_inventory', utility)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    sources = module.source_manifest(manifest.parent, ws, repo, a.extra_input, cwd=repo)
    # Cargo target/build paths stay literal in copied manifests; reject any escape
    # and require every explicit Rust entry to be in the recorded snapshot.
    for name in sources:
        if pathlib.Path(name).name != 'Cargo.toml':
            continue
        data = tomllib.loads((repo/name).read_text())
        references = []
        build = data.get('package', {}).get('build')
        if isinstance(build, str):
            references.append(build)
        targets = [data.get('lib', {})]
        for kind in ('bin', 'example', 'test', 'bench'):
            targets.extend(data.get(kind, []))
        references.extend(target['path'] for target in targets if 'path' in target)
        for reference in references:
            path = pathlib.Path(reference)
            # The manifest keeps the caller's spelling; absolute forms differ by host.
            # A single separator is rooted even when modern ntpath.isabs says False.
            # Drive-prefixed relative paths are resolved from Windows drive state,
            # not the copied crate, so they are not repository-local entries.
            drive, _ = ntpath.splitdrive(reference)
            absolute = bool(drive) or reference.startswith(('/', '\\')) or path.is_absolute() or ntpath.isabs(reference)
            if absolute:
                raise ValueError('absolute Cargo target/build paths are unsupported: '+reference)
            target = ((repo/name).parent/path).resolve()
            recorded = target.relative_to(repo).as_posix() if target.is_relative_to(repo) else None
            if recorded is None or recorded not in sources:
                raise ValueError('Cargo target/build source is outside the recorded snapshot: '+reference)
    for name in sources:
        path = repo/name
        if path.is_symlink() or path.suffix in {'.so', '.rlib', '.o', '.a', '.dylib', '.dll', '.exe', '.wasm', '.bin'} or name.startswith(('evidence/original/', 'evidence/dependencies/')):
            raise ValueError('reference executables/binary build inputs or symlinks are not supported: '+name)
    for extra in a.extra_input:
        if extra.resolve().is_dir() and output.is_relative_to(extra.resolve()):
            raise ValueError('output overlaps an extra-input source directory')
    # Every local path dependency / workspace member must have its manifest in the copy.
    for name in list(sources):
        if pathlib.Path(name).name != 'Cargo.toml':
            continue
        data = tomllib.loads((repo/name).read_text())
        def walk(value):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k == 'path' and isinstance(v, str) and pathlib.Path(v).suffix != '.rs':
                        # The copied manifest keeps this spelling, so an absolute path would
                        # build the live directory instead of the recorded snapshot.
                        # ntpath.splitdrive also catches drive-relative spellings such as C:dep.
                        if v.startswith(('/', '\\')) or pathlib.Path(v).is_absolute() or ntpath.splitdrive(v)[0]:
                            raise ValueError('absolute Cargo path dependencies are unsupported: '+v)
                        target = (repo/name).parent/v/'Cargo.toml'
                        if not target.resolve().is_relative_to(repo):
                            raise ValueError('Cargo path dependency is outside the recorded snapshot: '+v)
                        if target.is_file() and str(target.resolve().relative_to(repo)) not in sources:
                            raise ValueError('unrecorded local path dependency; supply --extra-input: '+str(target))
                    walk(v)
            elif isinstance(value, list):
                for v in value: walk(v)
        # [package] holds no dependencies (`build` is checked above; Cargo ignores metadata).
        walk({k: v for k, v in data.items() if k != 'package'})
    for member in workspace_toml.get('workspace', {}).get('members', []):
        hits = list(ws.glob(member))
        if not hits or any(str((d/'Cargo.toml').relative_to(repo)) not in sources for d in hits):
            raise ValueError('unrecorded workspace member; supply --extra-input: '+member)
    tool_root = pathlib.Path(cache_root or pathlib.Path.home()/'.cache/solana')
    tools = tool_root/a.tools_version/'platform-tools'; tool_hashes = {}
    for name, record in policy['selected_files'].items():
        f = tools/name
        if not f.is_file() or sha(f) != record['sha256']:
            raise ValueError('measured tool/sysroot bytes differ: '+str(f))
        tool_hashes[str(f)] = sha(f)
    for name, record in policy['extra_environment_tools'].items():
        f = tools/name
        if not f.is_file() or f.resolve() != (tools/record['resolved_relative_path']).resolve() or sha(f) != record['sha256']:
            raise ValueError('measured environment tool differs: '+str(f))
        tool_hashes[str(f)] = sha(f)
    strip = tool_root/policy['strip_tools_version']/'platform-tools/llvm/bin/llvm-objcopy'
    if not strip.is_file() or sha(strip) != policy['strip_sha256']:
        raise ValueError('measured v1.52 strip bytes differ')
    tool_hashes[str(strip)] = sha(strip)
    lib = crate_toml.get('lib', {}).get('name', '')
    if not lib or '/' in lib or '\\' in lib or 'cdylib' not in crate_toml.get('lib', {}).get('crate-type', []):
        raise ValueError('an explicit cdylib library name is required')
    copied = output/'source'; copied_manifest = copied/manifest.relative_to(repo)
    updates = {'CARGO_HOME': str(output/'cargo-home'), 'CARGO_TARGET_DIR': str(output/'target'),
               'RUSTUP_HOME': str(output/'rustup'), 'CARGO_NET_OFFLINE': 'true',
               'RUSTC': str(tools/'rust/bin/rustc'), 'RUSTDOC': str(tools/'rust/bin/rustdoc'),
               'CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS': policy['target_rustflags'],
               **{k: str(tools/'llvm/bin'/v) for k, v in {'CC':'clang','AR':'llvm-ar','OBJDUMP':'llvm-objdump','OBJCOPY':'llvm-objcopy'}.items()}}
    command = [str(tools/'rust/bin/cargo'), 'build', '--manifest-path', str(copied_manifest), '--release',
               '--target', policy['target'], '--locked', '--offline', '--verbose']
    return {'scope': 'Proposed controlled research source build; no runtime/identity acceptance',
            'program': a.program, 'tools_version': a.tools_version, 'manifest': str(manifest),
            'workspace': str(ws), 'repository': str(repo), 'output': str(output), 'source_sha256': sources,
            'extra_inputs': [str(x.resolve()) for x in a.extra_input], 'profile': {**PROFILE, 'opt-level': 3},
            'features': 'Cargo default features as declared; no CLI feature/CPU overrides',
            'command': command, 'cwd': str(copied), 'environment': updates, 'cache_source': str(cargo_source),
            'compiled_binary': str(output/'target'/policy['target']/'release'/(lib+'.so')),
            'artifact': str(output/'artifacts'/a.artifact_name), 'strip_command': [str(strip), '--strip-all', str(output/'unstripped.so'), str(output/'artifacts'/a.artifact_name)],
            'tool_sha256': tool_hashes, 'policy_sha256': sha(policy_path),
            'target_spec': policy.get('target_spec', {}), 'target_adaptation': policy.get('target_adaptation', {}),
            'distribution_version_md': (tools/'version.md').read_text() if (tools/'version.md').is_file() else None, 'source_manifest_utility_sha256': sha(utility),
            'adapter_sha256': sha(pathlib.Path(__file__)), 'global_alias_mutated': False,
            'comparison_reference': str(repo/'evidence/original'/a.program/'deployed.so'),
            'comparison_reference_read_before_compile': False, 'dry_run': a.dry_run,
            'provenance_limit': 'Known local inputs and selected tool/sysroot closure; extra build assets must be explicit; not a hermetic or historical compiler proof'}


def verify_registry(lock, cargo_home):
    """The measured archive/member check, over each locally available locked registry root.

    Unavailable platform-only packages remain recorded, not treated as absent target dependencies.
    Cargo may extract an authenticated archive into the private cache during compilation.
    """
    records = []
    for package in tomllib.loads(lock.read_text()).get('package', []):
        if not package.get('source', '').startswith('registry+'):
            continue
        name = package['name']+'-'+package['version']; found = []
        for source in sorted((cargo_home/'registry/src').glob('*/'+name)):
            index = source.parent.name; archive = cargo_home/'registry/cache'/index/(name+'.crate')
            if not archive.is_file() or sha(archive) != package['checksum']:
                raise ValueError('missing/mismatched locked archive for source cache: '+name)
            members = {}
            with tarfile.open(archive) as stream:
                for member in stream:
                    if not member.isfile():
                        continue
                    parts = pathlib.Path(member.name).parts
                    if not parts or parts[0] != name or '..' in parts:
                        raise ValueError('unsafe registry archive member: '+name)
                    relative = str(pathlib.Path(*parts[1:])); data = stream.extractfile(member).read()
                    if (source/relative).read_bytes() != data:
                        raise ValueError('cached dependency source differs from locked archive: '+name+'/'+relative)
                    members[relative] = hashlib.sha256(data).hexdigest()
            actual = {str(p.relative_to(source)) for p in source.rglob('*') if p.is_file()}
            if actual-set(members)-{'.cargo-ok'}:
                raise ValueError('unrecorded cached dependency source members: '+name)
            found.append({'index': index, 'archive_sha256': package['checksum'], 'verified_files': len(members),
                          'member_inventory_sha256': hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
        for archive in sorted((cargo_home/'registry/cache').glob('*/'+name+'.crate')):
            if sha(archive) != package['checksum']:
                raise ValueError('locked archive checksum mismatch: '+name)
        records.append({'package': name, 'lock_checksum': package['checksum'], 'available_source_roots': found})
    return records


def artifact_record(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 64 or data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('compiler/strip output is not ELF64 little endian')
    header = {'machine': struct.unpack_from('<H', data, 18)[0], 'flags': struct.unpack_from('<I', data, 48)[0]}
    if header != {'machine': 263, 'flags': 0}:
        raise ValueError('output header differs from measured generic V0')
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'header': header}


def exit_code(code):
    return code if 0 <= code <= 255 else min(255, 128+abs(code)) if code < 0 else 1


def execute(planned, env, *, runner=subprocess.run):
    """Only this function can spawn Cargo/strip; tests inject a nonexecuting runner."""
    validate_environment(env)
    output = pathlib.Path(planned['output']); repo = pathlib.Path(planned['repository'])
    reject_configs([pathlib.Path(planned['manifest']).parent, repo, output.parent], pathlib.Path(planned['cache_source']))
    output.mkdir(parents=True, exist_ok=False)
    record = {**planned, 'dry_run': False, 'compile_returncode': None, 'strip_returncode': None,
              'wrapper_exit_status': None, 'comparison_reference_read': False, 'stage': 'prepare'}
    def save(): (output/'build-attempt.json').write_text(json.dumps(record, indent=2)+'\n')
    save(); started = time.time()
    try:
        for name, digest in planned['source_sha256'].items():
            source = repo/name
            if sha(source) != digest: raise ValueError('source changed after planning: '+name)
            dest = output/'source'/name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, dest)
        shutil.copytree(pathlib.Path(planned['cache_source'])/'registry', output/'cargo-home/registry', symlinks=False)
        (output/'rustup').mkdir(); (output/'artifacts').mkdir()
        # Revalidate pinned tools immediately before spawning, without clearing overrides.
        for name, digest in planned['tool_sha256'].items():
            if sha(pathlib.Path(name)) != digest: raise ValueError('tool changed after planning: '+name)
        reject_configs([pathlib.Path(planned['cwd']), pathlib.Path(planned['command'][planned['command'].index('--manifest-path')+1]).parent], output/'cargo-home')
        validate_environment(env); child_env = dict(env); child_env.update(planned['environment'])
        copied_lock = output/'source'/pathlib.Path(planned['workspace']).relative_to(repo)/'Cargo.lock'
        record['registry_before'] = verify_registry(copied_lock, output/'cargo-home')
        record['stage'] = 'compile'; save()
        with (output/'build.log').open('w') as log:
            result = runner(planned['command'], env=child_env, cwd=planned['cwd'], stdout=log, stderr=subprocess.STDOUT)
        record['compile_returncode'] = result.returncode
        record['registry_after'] = verify_registry(copied_lock, output/'cargo-home')
        record['build_log_sha256'] = sha(output/'build.log')
        utility = repo/'scripts/build_source_manifest.py'
        if sha(utility) != planned['source_manifest_utility_sha256']:
            raise ValueError('source manifest utility changed during compilation')
        spec = importlib.util.spec_from_file_location('supported_builder_after_inventory', utility)
        inventory = importlib.util.module_from_spec(spec); spec.loader.exec_module(inventory)
        current = inventory.source_manifest(pathlib.Path(planned['manifest']).parent, pathlib.Path(planned['workspace']), repo,
                                            [pathlib.Path(p) for p in planned['extra_inputs']], cwd=repo)
        copied_repo = output/'source'
        copied = inventory.source_manifest(copied_repo/pathlib.Path(planned['manifest']).parent.relative_to(repo),
                                           copied_repo/pathlib.Path(planned['workspace']).relative_to(repo), copied_repo,
                                           [copied_repo/pathlib.Path(p).relative_to(repo) for p in planned['extra_inputs']], cwd=copied_repo)
        record.update(source_after_sha256=copied, caller_source_after_sha256=current,
                      source_unchanged=copied == current == planned['source_sha256'])
        if result.returncode != 0:
            record['wrapper_exit_status'] = exit_code(result.returncode); record['stage'] += '_failed'; return record['wrapper_exit_status']
        if not record['source_unchanged']: raise ValueError('source/lock changed during compilation')
        record['compiler_output'] = artifact_record(planned['compiled_binary'])
        shutil.copyfile(planned['compiled_binary'], output/'unstripped.so')
        strip_tool = pathlib.Path(planned['strip_command'][0])
        if sha(strip_tool) != planned['tool_sha256'][str(strip_tool)]: raise ValueError('strip tool changed during compilation')
        record['stage'] = 'strip'; save()
        with (output/'strip.log').open('w') as log:
            result = runner(planned['strip_command'], cwd=planned['cwd'], env=child_env, stdout=log, stderr=subprocess.STDOUT)
        record['strip_returncode'] = result.returncode; record['strip_log_sha256'] = sha(output/'strip.log')
        if result.returncode != 0:
            record['wrapper_exit_status'] = exit_code(result.returncode); record['stage'] += '_failed'; return record['wrapper_exit_status']
        # No capture is opened or hashed until successful compilation AND strip.
        record['stripped_output'] = artifact_record(planned['artifact'])
        record['stage'] = 'compare'; save()
        candidate = pathlib.Path(planned['artifact']).read_bytes()
        original = pathlib.Path(planned['comparison_reference']).read_bytes(); record['comparison_reference_read'] = True
        first = next((i for i, (x, y) in enumerate(zip(original, candidate)) if x != y), None)
        if first is None and len(original) != len(candidate): first = min(len(original), len(candidate))
        comparison = {'original_bytes': len(original), 'candidate_bytes': len(candidate),
                      'original_sha256': hashlib.sha256(original).hexdigest(), 'candidate_sha256': hashlib.sha256(candidate).hexdigest(),
                      'full_byte_equality': original == candidate, 'first_difference': first,
                      'different_positions_in_shared_length': sum(x != y for x, y in zip(original, candidate)),
                      'length_difference': len(candidate)-len(original)}
        record.update(stage='complete', wrapper_exit_status=0, elapsed_seconds=time.time()-started)
        report = {**record, 'comparison': comparison, 'historical_compiler_identity_proven': False, 'runtime_executions': 0}
        (output/'build-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
        record['stage'] = 'complete'; record['wrapper_exit_status'] = 0; return 0
    except Exception as error:
        record['error'] = {'type': type(error).__name__, 'message': str(error)}
        record['wrapper_exit_status'] = 1; return 1
    finally:
        for filename, key in [('build.log','build_log_sha256'),('strip.log','strip_log_sha256')]:
            if (output/filename).is_file(): record[key] = sha(output/filename)
        record['elapsed_seconds'] = time.time()-started; save()


def main(arguments=None):
    a = parser().parse_args(arguments); env = dict(os.environ)
    try:
        result = plan(a, repository(), env)
    except (ValueError, FileNotFoundError, KeyError, StopIteration) as error:
        print(str(error), file=sys.stderr); return 2
    if a.dry_run:
        print(json.dumps(result, indent=2)); return 0
    return execute(result, env)


if __name__ == '__main__':
    raise SystemExit(main())
