#!/usr/bin/env python3
"""Replay the selected main-Pump checkpoint with its captured loader accounts."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tarfile

from verify_pump_main_checkpoint import PACKAGE, ROOT, sha, verify


def _create_missing_directories(path, created_directories):
    missing = []
    current = path
    while not current.exists():
        if current.is_symlink():
            raise ValueError('Compiled source parent symlink')
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir()
        created_directories.append(directory)


def _roll_back_created_paths(created_files, created_directories):
    failures = []
    for path in reversed(created_files):
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            failures.append((path, error))
    for path in reversed(created_directories):
        try:
            path.rmdir()
        except FileNotFoundError:
            pass
        except OSError as error:
            failures.append((path, error))
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=2)
    parser.add_argument('--shard', type=int, default=1)
    parser.add_argument('--shards', type=int, choices=range(1, 5), default=1)
    args = parser.parse_args()
    assert 1 <= args.shard <= args.shards
    verify(ROOT)
    selected = json.loads((ROOT / 'repro/status.json').read_text())['pump']
    if selected['candidate_artifact'] in ['repro/pump/canonical-frontier-20261028/candidate.so', 'research/pump-create-used-boundaries-20261028/artifacts/candidate.so', 'research/pump-final-composition-673-20261028/artifacts/candidate.so', 'research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so', 'research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so']:
        if not __debug__:
            raise SystemExit('Replay requires normal Python; do not use -O.')
        package = (ROOT / selected['candidate_artifact']).parent
        if package.name == 'artifacts':
            package = package.parent
        comparison = package / 'builds/primary/build-comparison.json'
        record = json.loads(comparison.read_text())
        prefix = next(iter(record['source_sha256'])).split('/source/', 1)[0] + '/source'
        workspace = ROOT / prefix
        workspace.resolve().relative_to(ROOT.resolve())
        # Use the actual compiled workspace and receipt. The sealed source
        # archive materializes that same workspace in a clean CI checkout.
        archive_name = 'compiled-workspace.tar.gz' if selected['candidate_artifact'] in ['research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so', 'research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so'] else 'compiled-source.tar.gz'
        created_files = []
        created_directories = []
        try:
            with tarfile.open(package / 'builds/primary' / archive_name) as archive:
                for item in archive:
                    path = Path(item.name)
                    if not item.isfile() or path.is_absolute() or '..' in path.parts:
                        raise ValueError('Unsafe compiled source archive member')
                    destination = workspace / path
                    if not destination.resolve().is_relative_to(workspace.resolve()):
                        raise ValueError('Compiled source destination escapes workspace')
                    if any(parent.is_symlink() for parent in destination.parents if parent.is_relative_to(workspace)):
                        raise ValueError('Compiled source parent symlink')
                    data = archive.extractfile(item).read()
                    import hashlib
                    if hashlib.sha256(data).hexdigest() != record['source_sha256'][str(destination.relative_to(ROOT))]:
                        raise ValueError('Compiled source archive binding')
                    if destination.exists():
                        if destination.is_symlink() or destination.read_bytes() != data:
                            raise ValueError('Existing compiled workspace differs')
                    else:
                        _create_missing_directories(destination.parent, created_directories)
                        created_files.append(destination)
                        destination.write_bytes(data)
            args.output = args.output.resolve()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/pump_validate_parallel.py'),
                            '--candidate', str(ROOT / selected['candidate_artifact']),
                            '--source-directory', str(workspace / 'programs/pump'),
                            '--build-comparison', str(comparison), '--output', str(args.output),
                            '--captured-loader', '--workers', str(args.workers),
                            '--shard', str(args.shard), '--shards', str(args.shards)], cwd=ROOT, check=True)
            if selected['candidate_artifact'] in ['research/pump-final-composition-673-20261028/artifacts/candidate.so', 'research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so', 'research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so']:
                subprocess.run([sys.executable, '-O', '-B', str(ROOT / 'scripts/pump_strict_ordered_logs.py'),
                                '--report', str(args.output), '--candidate', str(ROOT / selected['candidate_artifact']),
                                '--output', str(args.output) + '.strict-logs.json'], cwd=ROOT, check=True)
            verify(ROOT)
        except BaseException:
            for path, error in _roll_back_created_paths(created_files, created_directories):
                print(f'warning: could not remove created path {path}: {error}', file=sys.stderr)
            raise
        return
    package = ROOT / PACKAGE
    checkpoint = json.loads((package / 'CHECKPOINT.json').read_text())
    record = json.loads((package / 'canonical-build.json').read_text())
    # This is an explicit portable view of a proven identical source copy,
    # not a claim that CI executed another compiler invocation.
    record['portable_source_binding'] = {
        'kind': 'verified-equal-canonical-primary-source',
        'origin_build_record': PACKAGE + '/canonical-build.json',
        'origin_build_record_sha256': sha(package / 'canonical-build.json'),
        'original_compiled_source_sha256': record['source_sha256'],
    }
    record['source_directory'] = str(ROOT / 'programs/pump')
    record['source_sha256'] = {
        'programs/pump/' + name: digest
        for name, digest in checkpoint['primary_source_sha256'].items()
    }
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    binding = args.output.with_name(args.output.name + '.source-binding.json')
    binding.write_text(json.dumps(record, indent=2) + '\n')
    command = [sys.executable, '-B', str(ROOT / 'scripts/pump_validate_parallel.py'),
               '--candidate', str(package / 'candidate.so'),
               '--source-directory', str(ROOT / 'programs/pump'),
               '--build-comparison', str(binding), '--output', str(args.output),
               '--captured-loader', '--workers', str(args.workers),
               '--shard', str(args.shard), '--shards', str(args.shards)]
    subprocess.run(command, cwd=ROOT, check=True)
    verify(ROOT)


if __name__ == '__main__':
    main()
