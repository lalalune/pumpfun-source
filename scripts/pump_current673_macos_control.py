#!/usr/bin/env python3
"""Reproduce archived673 with its unchanged portable cold builder on native macOS."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
import argparse
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / 'research/pump-current673-macos-qualification/inputs.json'
SOURCE_DIRECTORY = ROOT / 'research/pump-final-composition-673-20261028/source'
WORK = ROOT / 'work/pump-current673-macos-control'
EVIDENCE = WORK / 'evidence'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def download_archive(url, expected_sha256, destination):
    """Download an archive without publishing bytes that fail authentication."""
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                prefix='.' + destination.name + '.', dir=destination.parent,
                delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(url, timeout=120) as response:
                shutil.copyfileobj(response, output)
        observed = sha(temporary)
        if observed != expected_sha256:
            raise ValueError(destination.stem + ' archive hash mismatch')
        # Link only to an absent name: a file created during the download
        # belongs to its writer and must not be replaced.
        os.link(temporary, destination)
        return observed
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def inspect(source_directory=None):
    spec = json.loads(SPEC.read_text())
    cold = ROOT / spec['cold_package']
    assert sha(cold / 'build.py') == spec['builder_sha256']
    assert sha(cold / 'build-inputs.json') == spec['build_inputs_sha256']
    assert {p.name: sha(p) for p in (cold / 'tools').iterdir() if p.is_file()} == spec['tools_sha256']
    definition = importlib.util.spec_from_file_location('current673_source_manifest', cold / 'tools/build_source_manifest.py')
    module = importlib.util.module_from_spec(definition)
    definition.loader.exec_module(module)
    # The retained spec records the original programs/pump locator. Future runs
    # select the authenticated archived673 tree without rewriting that receipt.
    source = Path(source_directory or SOURCE_DIRECTORY).resolve()
    manifest = module.source_manifest(source, source, ROOT, cwd=source)
    actual = {str((ROOT / name).relative_to(source)): digest for name, digest in manifest.items()}
    expected = json.loads((cold / 'build-inputs.json').read_text())
    assert actual == expected['source_inputs'], 'Selected source differs from frozen673 inputs'
    assert sha(ROOT / 'evidence/original/pump/deployed.so') == spec['original_sha256']
    assert expected['comparison']['candidate_sha256'] == spec['expected']['candidate_sha256']
    assert expected['unstripped_sha256'] == spec['expected']['unstripped_sha256']
    return spec, cold, source, actual, expected


def run(name, command, env=None):
    command = [str(x) for x in command]
    log = EVIDENCE / (name + '.log')
    with log.open('w') as f:
        process = subprocess.run(command, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
    with (EVIDENCE / 'commands.jsonl').open('a') as f:
        f.write(json.dumps({'name': name, 'command': command, 'returncode': process.returncode}) + '\n')
    if process.returncode:
        print(log.read_text()[-16000:], flush=True)
    process.check_returncode()


def retain(build):
    if build.is_dir():
        for name in ['candidate.so', 'unstripped.so', 'executed-builder.py', 'build-attempt.json',
                     'build-comparison.json', 'registry-authentication.json', 'target-library-profile-files.json']:
            if (build / name).is_file():
                shutil.copyfile(build / name, EVIDENCE / name)
        for name in ['build.log', 'physical-source-calls.jsonl']:
            if (build / name).is_file():
                (EVIDENCE / (name + '.gz')).write_bytes(gzip.compress((build / name).read_bytes(), mtime=0))
        if (build / 'source').is_dir():
            # Pin the gzip header mtime: the archive is hashed into the
            # manifest, and a wall-clock header made identical inputs hash
            # differently per run.
            with open(EVIDENCE / 'compiled-source.tar.gz', 'wb') as raw_archive, tarfile.open(
                    fileobj=gzip.GzipFile(filename='', fileobj=raw_archive, mode='wb', mtime=0),
                    mode='w') as archive:
                for path in sorted((build / 'source').rglob('*')):
                    if path.is_file():
                        archive.add(path, arcname=path.relative_to(build / 'source'), recursive=False)
    write(EVIDENCE / 'MANIFEST.json', {p.relative_to(EVIDENCE).as_posix(): sha(p)
          for p in sorted(EVIDENCE.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true', help='Authenticate frozen local inputs only; no download/build')
    parser.add_argument('--source-directory', type=Path, default=SOURCE_DIRECTORY,
                        help='Archived673 primary source; all65 existing hashes must match')
    args = parser.parse_args()
    spec, cold, source, source_before, expected = inspect(args.source_directory)
    if args.inspect:
        print(json.dumps({'source_files': len(source_before), 'authenticated_cold_builder': spec['builder_sha256'],
                          'expected': spec['expected'], 'source_directory': str(source),
                          'scope': 'historical673 control; not maintained current-source qualification'}, indent=2))
        return
    assert platform.system() == 'Darwin' and platform.machine() == 'arm64', 'Native Apple Silicon macOS required'
    assert sys.version_info >= (3, 12), 'Python 3.12+ required for safe tar extraction'
    EVIDENCE.mkdir(parents=True, exist_ok=False)
    for path, name in [(SPEC, 'inputs.json'), (Path(__file__), 'controller.py'),
                       (ROOT / '.github/workflows/qualify-pump-macos-v144.yml', 'workflow.yml'),
                       (cold / 'build-inputs.json', 'build-inputs.json')]:
        shutil.copyfile(path, EVIDENCE / name)
    write(EVIDENCE / 'source-before.json', source_before)
    write(EVIDENCE / 'host.json', {'system': platform.system(), 'machine': platform.machine(), 'python': sys.version,
                                  'primary_source_directory': str(source),
                                  'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()})
    build = WORK / 'control'
    try:
        downloads = {}
        for label, pin in spec['archives'].items():
            archive_path = WORK / (label + '.tar.bz2')
            download_archive(pin['url'], pin['sha256'], archive_path)
            destination = WORK / label
            destination.mkdir()
            with tarfile.open(archive_path) as archive:
                archive.extractall(destination, filter='data')
            downloads[label] = dict(pin, observed_sha256=sha(archive_path))
            write(EVIDENCE / 'downloads.json', downloads)
        sdk = WORK / 'macos'
        libraries = WORK / 'linux/rust/lib/rustlib/sbpf-solana-solana/lib'
        actual_libraries = {p.name: {'sha256': sha(p), 'mode': p.stat().st_mode & 0o777}
                            for p in libraries.iterdir() if p.is_file()}
        assert actual_libraries == expected['target_libraries_sha256'], 'Raw Linux SBPF libraries differ'
        native = {'rustc': sdk / 'rust/bin/rustc', 'cargo': sdk / 'rust/bin/cargo',
                  'objcopy': sdk / 'llvm/bin/llvm-objcopy', 'clang': sdk / 'llvm/bin/clang', 'ar': sdk / 'llvm/bin/llvm-ar'}
        assert {name: sha(path) for name, path in native.items()} == expected['tool_sha256'], 'Native SDK tools differ'
        registry = WORK / 'cargo-home'
        env = dict(os.environ, CARGO_HOME=str(registry), RUSTC=str(native['rustc']),
                   PATH=str(sdk / 'rust/bin') + os.pathsep + os.environ['PATH'])
        # Fetch resolves locked packages; the frozen builder authenticates every
        # archive and extracted registry source file before compiling.
        run('fetch', [native['cargo'], 'fetch', '--locked', '--manifest-path', source / 'Cargo.toml'], env)
        run('cold-control', [sys.executable, '-B', cold / 'build.py', '--source-directory', source,
            '--sdk', sdk, '--cargo-home', registry, '--target-library-profile', 'linux-v1.44-sbpf',
            '--target-libraries', libraries, '--wrapper', cold / 'tools/pump_physical_source_wrapper.py', '--output', build])
        actual = {'candidate_sha256': sha(build / 'candidate.so'), 'unstripped_sha256': sha(build / 'unstripped.so')}
        assert actual == spec['expected'], 'Complete current673 ELF hashes did not reproduce'
        receipt = json.loads((build / 'build-attempt.json').read_text())
        assert all(receipt[k] for k in ['cold_empty_target', 'source_unchanged', 'tools_unchanged',
            'sdk_rust_libraries_unchanged', 'registry_sources_unchanged', 'target_libraries_unchanged', 'qualified_image_hashes_equal'])
        assert inspect(source)[3] == source_before
        write(EVIDENCE / 'RESULT.json', {'status': 'reproduced', 'base_commit': spec['base_commit'],
            **actual, 'cold_empty_target': True, 'source_files': len(source_before),
            'limits': 'Unchanged control only. No new census, runtime, candidate or original whole-ELF identity claim.'})
        print(json.dumps(actual, indent=2), flush=True)
    finally:
        retain(build)


if __name__ == '__main__':
    main()
