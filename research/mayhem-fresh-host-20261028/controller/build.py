#!/usr/bin/env python3
"""Explicit offline Windows build from retained source and supplied SDK/vendor inputs."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def raw(path):
    data = path.read_bytes()
    return gzip.decompress(data) if path.suffix == '.gz' else data


def read(path):
    return json.loads(raw(path))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def safe(name):
    p = PurePosixPath(name)
    require(bool(name) and not p.is_absolute() and '..' not in p.parts and ':' not in name
            and '\\' not in name and p.as_posix() == name, 'invalid component path')
    return name


def pin(root, rows):
    seen = set()
    for row in rows:
        name = safe(row['path'])
        require(name not in seen, 'duplicate component')
        seen.add(name)
        path = root / name
        require(path.is_file() and not path.is_symlink(), 'nonregular component: ' + name)
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                'component differs: ' + name)


def vendor_check(root, package=HERE):
    records = read(package / 'vendor-inputs.json')['packages']
    for record in records:
        directory = root / safe(record['directory'])
        checksum = directory / '.cargo-checksum.json'
        require(sha(checksum) == record['checksum_file_sha256'], 'vendor checksum map differs')
        data = read(checksum)
        require(data['package'] == record['package_sha256']
                and len(data['files']) == record['file_count'], 'vendor package record differs')
        actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*')
                  if p.is_file() and p.name != '.cargo-checksum.json'}
        require(actual == set(data['files']), 'vendor file set differs')
        for name, digest in data['files'].items():
            path = directory / safe(name)
            require(not path.is_symlink() and sha(path) == digest, 'vendor source differs')
    return len(records)


def build(args):
    require(os.name == 'nt', 'Windows compiler and host linker required')
    sdk, target, vendor, vc, kit = [getattr(args, n).resolve() for n in
                                   ('sdk', 'target_sysroot', 'vendor', 'msvc', 'windows_sdk')]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status='STARTED', target_executions=0)
    start = time.monotonic()
    try:
        sdk_rows = read(HERE / 'sdk-components.json.gz')['files']
        target_rows = read(HERE / 'target-components.json')['files']
        pin(sdk, sdk_rows)
        pin(target.parent, target_rows)
        vendor_count = vendor_check(vendor)
        source = output / 'source/programs/mayhem'
        inputs = read(HERE / 'source-inputs.json')['source_files']
        for row in inputs:
            name = safe(row['path'])
            data = raw(HERE / 'sources' / (name + '.gz'))
            require(len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'],
                    'retained source differs')
            path = source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        before = {r['path']: r['sha256'] for r in inputs}
        cargo_home = output / 'cargo-home'
        cargo_home.mkdir()
        (cargo_home / 'config.toml').write_text(
            '[source.crates-io]\nreplace-with = "locked-vendor"\n[source.locked-vendor]\ndirectory = '
            + json.dumps(str(vendor)) + '\n[net]\noffline = true\n', encoding='utf-8', newline='\n')
        temp = output / 'temp'
        temp.mkdir()
        system = Path(os.environ['SystemRoot'])
        env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'SystemDrive', 'COMSPEC',
                                         'PROCESSOR_ARCHITECTURE') if k in os.environ}
        extra = dict(
            PATH=os.pathsep.join(map(str, [sdk / 'rust/bin', sdk / 'llvm/bin',
                vc / 'bin/Hostx64/x64', kit / 'bin' / args.kit_version / 'x64', system / 'System32'])),
            LIB=os.pathsep.join(map(str, [vc / 'lib/x64', kit / 'Lib' / args.kit_version / 'ucrt/x64',
                                         kit / 'Lib' / args.kit_version / 'um/x64'])),
            INCLUDE=os.pathsep.join(map(str, [vc / 'include', *[
                kit / 'Include' / args.kit_version / n for n in ('ucrt', 'shared', 'um', 'winrt')]])),
            RUSTC=str(sdk / 'rust/bin/rustc.exe'), RUSTDOC=str(sdk / 'rust/bin/rustdoc.exe'),
            CARGO_HOME=str(cargo_home), CARGO_TARGET_DIR=str(output / 'target'), CARGO_NET_OFFLINE='true',
            CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS='-Zremap-cwd-prefix= --sysroot=' + str(target),
            CC_sbpf_solana_solana=str(sdk / 'llvm/bin/clang.exe'),
            AR_sbpf_solana_solana=str(sdk / 'llvm/bin/llvm-ar.exe'),
            CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER=str(vc / 'bin/Hostx64/x64/link.exe'),
            TEMP=str(temp), TMP=str(temp))
        records = output / 'wrapper-records'
        records.mkdir()
        wrapper = output / 'wrapper.exe'
        wrapper_source = HERE / 'wrapper.rs'
        metadata_map, path_map = HERE / 'metadata-map.tsv', HERE / 'path-map.tsv'
        linker_source, ordered, default = HERE / 'linker.rs', HERE / 'ordered-native.ld', HERE / 'default.ld'
        pinned = {p: sha(p) for p in (wrapper_source, metadata_map, path_map, linker_source, ordered, default)}
        require(sha(metadata_map) == 'fca25424ff3852c36c0c8009c7547f9ef027fbc660de37f141f4cb1c7ae725b5', 'metadata map differs')
        require(sha(path_map) == '20bcd9d6abe23a0e49acc5e5b558923bc64fbb46dbf6b4f19a9e38ccae275312', 'path map differs')
        compile_command = [str(sdk / 'rust/bin/rustc.exe'), '--crate-name', 'metadata_relative_wrapper',
                           '--edition=2021', '-C', 'opt-level=2', str(wrapper_source), '-o', str(wrapper)]
        host_env = dict(env, **extra)
        compiled = subprocess.run(compile_command, env=host_env, capture_output=True, timeout=120,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        (output / 'wrapper-compile.stdout.log').write_bytes(compiled.stdout)
        (output / 'wrapper-compile.stderr.log').write_bytes(compiled.stderr)
        wrapper_build = dict(command=compile_command, returncode=compiled.returncode,
                             source_sha256=pinned[wrapper_source], compiler_sha256=sha(sdk / 'rust/bin/rustc.exe'),
                             wrapper_sha256=sha(wrapper) if wrapper.is_file() else None)
        save(output / 'wrapper-compile-result.json', wrapper_build)
        require(compiled.returncode == 0, 'host wrapper compilation failed')
        wrapper_hash = sha(wrapper)
        linker = output / 'linker.exe'
        linker_command = [str(sdk / 'rust/bin/rustc.exe'), '--crate-name', 'qualified_linker_wrapper',
                          '--edition=2021', '-C', 'opt-level=2', str(linker_source), '-o', str(linker)]
        linked_wrapper = subprocess.run(linker_command, env=host_env, capture_output=True, timeout=120,
                                        creationflags=subprocess.CREATE_NO_WINDOW)
        (output / 'linker-compile.stdout.log').write_bytes(linked_wrapper.stdout)
        (output / 'linker-compile.stderr.log').write_bytes(linked_wrapper.stderr)
        linker_build = dict(command=linker_command, returncode=linked_wrapper.returncode,
                            source_sha256=pinned[linker_source], compiler_sha256=sha(sdk / 'rust/bin/rustc.exe'),
                            wrapper_sha256=sha(linker) if linker.exists() else None)
        save(output / 'linker-compile-result.json', linker_build)
        require(linked_wrapper.returncode == 0, 'linker wrapper compilation failed')
        linker_hash = sha(linker)
        extra.update(RUSTC_WRAPPER=str(wrapper), MAYHEM_METADATA_MODE='published-with-paths-relative',
                     MAYHEM_PATH_MAP=str(path_map), MAYHEM_METADATA_MAP=str(metadata_map),
                     MAYHEM_WRAPPER_RECORDS=str(records),
                     MAYHEM_LINKER_REAL=str(sdk / 'rust/lib/rustlib/x86_64-pc-windows-msvc/bin/rust-lld.exe'),
                     MAYHEM_LINKER_DEFAULT=str(default), MAYHEM_LINKER_SCRIPT=str(ordered),
                     MAYHEM_LINKER_OUTPUT=str(output / 'link'))
        historical = read(HERE / 'historical-macro.json')
        host_root = args.historical_macro_directory.resolve()
        historical = dict(path=str(host_root / safe(historical['macro']['path'])), sha256=historical['macro']['sha256'], host_dependencies={str(host_root / safe(n)):h for n,h in historical['host_dependencies'].items()})
        require(sha(Path(historical['path'])) == historical['sha256'], 'historical macro differs')
        require(all(sha(Path(n)) == h for n, h in historical['host_dependencies'].items()), 'historical host dependencies differ')
        extra.update(MAYHEM_HISTORICAL_MACRO=historical['path'], MAYHEM_HISTORICAL_DEPS=str(Path(historical['path']).parent / 'deps'))
        env.update(extra)
        tools = [sdk / 'rust/bin/rustc.exe', sdk / 'rust/bin/cargo.exe',
                 sdk / 'rust/bin/rustc_driver-4c05705140f85a08.dll', sdk / 'llvm/bin/llvm-ar.exe',
                 sdk / 'llvm/bin/clang.exe', sdk / 'llvm/bin/llvm-objcopy.exe',
                 sdk / 'rust/lib/rustlib/x86_64-pc-windows-msvc/bin/rust-lld.exe',
                 vc / 'bin/Hostx64/x64/link.exe', vc / 'bin/Hostx64/x64/cl.exe']
        checked = {str(p): sha(p) for p in tools}
        original = read(HERE / 'host-tools.json')
        # Locators may differ; executable names are unique in this checked cohort.
        expected = {n.replace('\\', '/').split('/')[-1]: h for n, h in original.items()}
        require(len(expected) == len(original), 'ambiguous executable identity')
        require({p.name: checked[str(p)] for p in tools} == expected, 'host/tool identity differs')
        command = [str(sdk / 'rust/bin/cargo.exe'), 'rustc', '--manifest-path', str(source / 'Cargo.toml'),
                   '--release', '--target', 'sbpf-solana-solana', '--locked', '--offline', '--verbose',
                   '--', '--remap-path-prefix=src/=programs/mayhem-program/src/',
                   '--remap-path-prefix=src/account_wrapper.rs=src/account_wrapper.rs', '-C', 'linker=' + str(linker)]
        launch = dict(command=command, cwd=str(source.parent.parent), environment_overrides=extra,
                      source_inputs=before, checked_executables=checked, vendor_packages=vendor_count, wrapper_build=wrapper_build,
                      linker_build=linker_build, pinned_controller_inputs={p.name:h for p,h in pinned.items()},
                      started_at=datetime.now(timezone.utc).isoformat(), target_directory_initially_absent=True,
                      scope='Fresh target dependencies and root; reused historical host macro/dependencies; native Windows compiler, Linux target libraries.')
        save(output / 'launch.json', launch)
        with (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
            process = subprocess.Popen(command, cwd=source.parent.parent, env=env, stdout=stdout,
                                       stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
            save(output / 'process.json', dict(pid=process.pid))
            code = process.wait()
        result.update(returncode=code, source_unchanged=before == {r['path']: sha(source / r['path']) for r in inputs},
                      root_invocations=(output / 'stderr.log').read_text(errors='replace').count('--crate-name mayhem_recovered '))
        require(code == 0 and result['source_unchanged'] and result['root_invocations'] == 1, 'build failed/incomplete')
        shutil.copyfile(output / 'target/sbpf-solana-solana/release/mayhem_recovered.so', output / 'symbols.so')
        strip = [str(sdk / 'llvm/bin/llvm-objcopy.exe'), '--strip-all',
                 str(output / 'symbols.so'), str(output / 'candidate-v154-strip.so')]
        stripped = subprocess.run(strip, env=env, capture_output=True, timeout=120,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
        (output / 'strip.stdout.log').write_bytes(stripped.stdout)
        (output / 'strip.stderr.log').write_bytes(stripped.stderr)
        result['strip'] = dict(command=strip, returncode=stripped.returncode)
        require(stripped.returncode == 0, 'strip failed')
        pin(sdk, sdk_rows)
        pin(target.parent, target_rows)
        vendor_check(vendor)
        require(all(sha(Path(n)) == h for n, h in checked.items()), 'executable changed')
        require(sha(wrapper) == wrapper_hash and sha(linker) == linker_hash and all(sha(p) == h for p, h in pinned.items()), 'wrapper/map/script changed')
        result['outputs'] = {p.name: dict(bytes=p.stat().st_size, sha256=sha(p)) for p in output.glob('*.so')}
        require(sha(Path(historical['path'])) == historical['sha256'] and all(sha(Path(n)) == h for n, h in historical['host_dependencies'].items()), 'historical macro/dependencies changed')
        result['historical_macro_dependencies_unchanged'] = True
        result['status'] = 'SUCCEEDED'
        result['comparison'] = 'Deferred until compilation is complete.'
    except Exception as error:
        result.update(status='FAILED', error_type=type(error).__name__, error=str(error))
        raise
    finally:
        result.update(elapsed_seconds=time.monotonic() - start, finished_at=datetime.now(timezone.utc).isoformat())
        result['logs'] = {p.name: dict(bytes=p.stat().st_size, sha256=sha(p)) for p in output.glob('*.log')}
        save(output / 'result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sdk', 'target-sysroot', 'vendor', 'msvc', 'windows-sdk', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--historical-macro-directory', type=Path, required=True)
    parser.add_argument('--kit-version', default='10.0.26100.0')
    print(json.dumps(build(parser.parse_args()), indent=2))
