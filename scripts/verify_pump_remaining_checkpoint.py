#!/usr/bin/env python3
"""Exact Pump compared-error checkpoint bridge; saved evidence only, no target/build."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[1]
MAIN = 'repro/pump/remaining-guards-main-fortyeight'
SCRATCH = 'repro/pump/remaining-guards-fortyeight'
MAIN_SEAL = '8ddf73d78e98005c8f68d189ada95add9690770bbd95c17ba42b25c6b0b95749'
SCRATCH_SEAL = '38558828d8187996e6f9f06db2b4054af7e65e29345a85f4417f71558312beba'
INNER_SEAL = '98c49ab1a0aaad83f51224df4aa44bbfb36308f53e8351dbed51298b87fdc67a'
CANDIDATE = '71ec4d8a646eefc82ba177afbc3d08552deadd65cf2f80ec280862eb768d059c'
SYMBOLS = '6edbf4dedf535dd0dec1199ab87a97d6d83b60fb2c1c3a5791feffc953a33cda'
README = '0cecc4be6aa0ed634cf3ecf83d70e6b557db12e84f8b0ae6cc20b9f50f8dd3e9'
SIDECAR_SHA256 = {'8ddf73d78e98005c8f68d189ada95add9690770bbd95c17ba42b25c6b0b95749': 'a439a2f4f979804301b815f237256e3d57a48e134b297ae059e6f287ae9ab34e', '38558828d8187996e6f9f06db2b4054af7e65e29345a85f4417f71558312beba': '6102dbf065c49ad742ed76c9b7d2c8d5027e18cce24eb133f83a18bfa39fd489', '98c49ab1a0aaad83f51224df4aa44bbfb36308f53e8351dbed51298b87fdc67a': '541d79be1a8189bcd65715337563c27f0433b3104aaa8e61042fb066c145c2c5'}

CACHE_NAMES = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}


class CheckpointError(Exception):
    pass


def check(ok, msg='checkpoint check failed'):
    # Explicit check instead of `assert`: `python -O` / PYTHONOPTIMIZE strips asserts,
    # which made tampered remaining-guards checkpoint evidence report PASS.
    if not ok:
        raise CheckpointError(msg)


def plain_path(path):
    """Reject symlinks in the supplied path and every existing ancestor."""
    path = Path(os.path.abspath(path))
    for parent in [*reversed(path.parents), path]:
        check(not stat.S_ISLNK(parent.lstat().st_mode), ('Symlink ancestry', str(parent)))
    return path


def content(path):
    path = plain_path(path)
    # Reject a FIFO, socket or device before opening it: a blocking open of
    # a FIFO with no writer never returns. The nonblocking open below keeps
    # a file swapped for a FIFO after this check from blocking as well; the
    # descriptor check then rejects it. Mirrors verify_current_checkpoint.
    assert stat.S_ISREG(path.lstat().st_mode), ('Nonregular path', str(path))
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                 | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(fd, 'rb') as stream:
        check(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), path)
        return stream.read()


def sha(path):
    return hashlib.sha256(content(path)).hexdigest()


def read(path):
    return json.loads(content(path))


def strict_package(package, expected):
    package = plain_path(package)
    check(package.is_dir(), package)
    raw = content(package / 'manifest.json')
    check(hashlib.sha256(raw).hexdigest() == expected, ('Known seal', str(package)))
    sidecar = (expected + '  manifest.json\n').encode()
    check(content(package / 'manifest.sha256') == sidecar, ('Exact sidecar', str(package)))
    check(sha(package / 'manifest.sha256') == SIDECAR_SHA256[expected])
    manifest = json.loads(raw)
    allowed_dirs = {''}
    for name in manifest:
        part = PurePosixPath(name)
        check(not part.is_absolute() and '..' not in part.parts and str(part) == name, name)
        check(name not in ('manifest.json', 'manifest.sha256'), name)
        allowed_dirs.update(str(p) for p in part.parents if str(p) != '.')
    files = set()
    def walk(directory):
        for item in os.scandir(directory):
            path = Path(item.path)
            name = path.relative_to(package).as_posix()
            mode = item.stat(follow_symlinks=False).st_mode
            check(not stat.S_ISLNK(mode), ('Symlink', name))
            check(item.name not in CACHE_NAMES and path.suffix not in ('.pyc', '.pyo'), ('Cache', name))
            if stat.S_ISDIR(mode):
                check(name in allowed_dirs, ('Unmanifested directory', name))
                walk(path)
            else:
                check(stat.S_ISREG(mode), ('Nonregular payload', name))
                files.add(name)
    walk(package)
    check(files == set(manifest) | {'manifest.json', 'manifest.sha256'}, ('Exact traversal', str(package)))
    for name, row in manifest.items():
        data = content(package / name)
        check(hashlib.sha256(data).hexdigest() == row['sha256'] and len(data) == row['bytes'], name)
    return manifest


def current_inputs(root, main):
    source = read(main / 'main/build-comparison.json')['source_sha256']
    check(len(source) == 37 and all(n.startswith('programs/pump/') and 'README' not in n for n in source))
    for name, digest in source.items():
        check(sha(root / name) == digest == sha(main / 'main/source' / name), name)
    check(sha(root / 'programs/pump/README.md') == sha(main / 'main/README.final.md') == README)
    helpers = read(main / 'promotion-control/inputs.json')['helpers']
    check(set(helpers) == {'scripts/analyze.py', 'scripts/compare.py', 'scripts/build_source_manifest.py', 'scripts/build_partial_candidate.py'})
    check(helpers['scripts/build_partial_candidate.py'] == 'bb683621ffc4297c58f030cb03da54484b7370b786fd8eda965a37f4b3198ee9')
    for name, digest in helpers.items():
        check(sha(root / name) == sha(main / 'promotion-control/helpers' / name) == digest, name)
    # Execute only the hash-checked canonical input scanner on the ACTUAL root.
    spec = importlib.util.spec_from_file_location('compared_current_input_scanner', root / 'scripts/build_source_manifest.py')
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    check(scanner.source_manifest(root / 'programs/pump', root / 'programs/pump', root, [], cwd=root) == source)
    return source


def verify(root):
    check(len(MAIN_SEAL) == 64, 'Pending actual main publication: no active route may use this draft')
    root = plain_path(root)
    main, wrapper = root / MAIN, root / SCRATCH
    strict_package(main, MAIN_SEAL)
    strict_package(wrapper, SCRATCH_SEAL)
    status = read(root / 'repro/status.json')['pump']
    check(status['candidate_artifact'] == MAIN + '/main/candidate.so')
    check(status['comparison_report'] == MAIN + '/main/build-comparison.json')
    check(status['build_log'] == MAIN + '/main/build.log')
    check(status['candidate_sha256'] == CANDIDATE and status['validated_cases'] == 9269)
    check(sha(main / 'main/candidate.so') == CANDIDATE and sha(main / 'main/unstripped.so') == SYMBOLS)
    check(sha(wrapper / 'inner-manifest.json') == INNER_SEAL)
    check(read(main / 'promotion-control/inputs.json')['scratch_seal'] == INNER_SEAL)
    source = current_inputs(root, main)
    children = []
    with tempfile.TemporaryDirectory(prefix='pump-current98-') as temporary:
        inner = Path(temporary).resolve() / 'inner'
        commands = [
            [sys.executable, '-B', str(wrapper / 'materialize.py'), '--expected-seal', SCRATCH_SEAL, '--output', str(inner)],
            [sys.executable, '-B', str(main / 'verify.py'), '--expected-seal', MAIN_SEAL, '--current-root', str(root), '--scratch', str(inner)],
        ]
        for command in commands:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            children.append({'command': command, 'returncode': result.returncode})
            check(result.returncode == 0, {'child': children[-1], 'stdout': result.stdout, 'stderr': result.stderr})
        strict_package(inner, INNER_SEAL)
        check(content(main / 'main/candidate.so') == content(inner / 'candidate.so'))
        check(content(main / 'main/unstripped.so') == content(inner / 'unstripped.so'))
        check(content(wrapper / 'inner-reader.py') == content(inner / 'verify.py'))
    strict_package(main, MAIN_SEAL)
    strict_package(wrapper, SCRATCH_SEAL)
    check(current_inputs(root, main) == source)
    return {'status': 'PASS', 'program': 'pump', 'candidate_sha256': CANDIDATE, 'source_inputs': 37,
            'main_seal': MAIN_SEAL, 'scratch_outer_seal': SCRATCH_SEAL, 'scratch_inner_seal': INNER_SEAL,
            'actual_current_sources_checked': True, 'current_helpers_exact': True,
            'unchanged_main_and_inner_saved_verifiers': children, 'lossless98_materialization': True,
            'differential_cases': 9269, 'surfpool_comparisons': 1024, 'application2006_runtime_coverage': 0,
            'target_executions': 0, 'builds': 0, 'original_global_failure_exits_rewritten': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo), indent=2))
