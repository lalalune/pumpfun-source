#!/usr/bin/env python3
"""Prepare the main-Pump reconstruction toolchain on this machine (macOS arm64).

  python3 reconstruction/toolchain/bootstrap.py [--sdk-check full|quick|skip] [--warm]

1. Verifies ~/.cache/solana/v1.44/platform-tools against v1.44-macos-inventory.json
   (every file hash by default). The SDK itself is not stored in git: its
   librustc_driver is 134 MB, above GitHub's 100 MB file limit. Install it with
   `cargo-build-sbf --tools-version v1.44` (or extract the official v1.44
   platform-tools-osx-aarch64 release there), then rerun this script.
2. Verifies the official Linux x86_64 v1.44 sbpf-solana-solana target libraries
   tracked in linux-v1.44-x86_64/ against harness/linux144-sbpf-target-libs.sha256.
3. Assembles the "hybrid144" identity toolchain (macOS v1.44 rustc + Linux v1.44
   sbpf target libraries) with harness/make_hybrid144.sh into
   $PUMP_RECON_HOME/toolchains/hybrid144 (default ~/.cache/pumpfun-reconstruction).
4. Creates the shared build-slot lock directory used by harness/fastbuild.py.
5. With --warm, builds programs/pump once and keeps its dependency artifacts as
   $PUMP_RECON_HOME/template-target-sbpf so later builds only recompile the
   pump crate.

Nothing is downloaded and nothing outside $PUMP_RECON_HOME is written, except
the --warm build's own work directory under $PUMP_RECON_HOME.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECON = HERE.parent
REPO = RECON.parent
HARNESS = RECON / 'harness'
HOME_CACHE = Path(os.environ.get('PUMP_RECON_HOME', Path.home() / '.cache/pumpfun-reconstruction'))
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
LINUX = HERE / 'linux-v1.44-x86_64'
MANIFEST = HARNESS / 'linux144-sbpf-target-libs.sha256'
HYBRID = HOME_CACHE / 'toolchains/hybrid144'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def check_sdk(mode):
    inventory = json.loads((HERE / 'v1.44-macos-inventory.json').read_text())['entries']
    problems = []
    for rel, row in inventory.items():
        path = SDK / rel
        if row['type'] == 'symlink':
            if not path.is_symlink() or os.readlink(path) != row['target']:
                problems.append(f'symlink {rel}')
        elif not path.is_file() or path.is_symlink():
            problems.append(f'missing {rel}')
        elif path.stat().st_size != row['bytes']:
            problems.append(f'size {rel}')
        elif mode == 'full' and sha(path) != row['sha256']:
            problems.append(f'sha256 {rel}')
    return len(inventory), problems


def check_linux_libs(root):
    expected = {}
    for number, line in enumerate(MANIFEST.read_text(encoding='utf-8').splitlines(), 1):
        match = re.fullmatch(r'([0-9a-f]{64})\s+(sbpf-solana-solana/lib/[A-Za-z0-9_-]+\.rlib)', line)
        if not match:
            return [f'invalid manifest line {number}']
        digest, rel = match.groups()
        if rel in expected:
            return [f'duplicate manifest path: {rel}']
        expected[rel] = digest
    if not expected:
        return ['empty library manifest']
    base = root / 'rust/lib/rustlib'
    library = base / 'sbpf-solana-solana/lib'
    if any(path.is_symlink() for path in (base, base / 'sbpf-solana-solana', library)):
        return ['target library directory is a symlink']
    problems = [rel for rel, digest in expected.items()
                if (base / rel).is_symlink() or not (base / rel).is_file() or sha(base / rel) != digest]
    actual = {path.relative_to(base).as_posix() for path in library.rglob('*')
              if path.is_file() or path.is_symlink()}
    problems.extend(f'unexpected library input: {rel}' for rel in sorted(actual - expected.keys()))
    return problems


def hybrid_ok():
    rust = HYBRID / 'rust'
    pairs = [(rust / 'bin/rustc', SDK / 'rust/bin/rustc')]
    pairs += [(lib, SDK / 'rust/lib' / lib.name) for lib in (rust / 'lib').glob('lib*.dylib')]
    if len(pairs) != 3 or any(not a.is_file() or sha(a) != sha(b) for a, b in pairs):
        return False
    host = rust / 'lib/rustlib/aarch64-apple-darwin'
    if not host.is_symlink() or host.resolve() != (SDK / 'rust/lib/rustlib/aarch64-apple-darwin').resolve():
        return False
    return not check_linux_libs(HYBRID)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sdk-check', choices=['full', 'quick', 'skip'], default='full')
    ap.add_argument('--warm', action='store_true', help='build programs/pump once to seed the shared dependency cache')
    args = ap.parse_args()

    if args.sdk_check != 'skip':
        total, problems = check_sdk(args.sdk_check)
        if problems:
            print(f'v1.44 SDK at {SDK} does not match the inventory ({len(problems)} of {total} entries):', file=sys.stderr)
            print('  ' + '\n  '.join(problems[:20]), file=sys.stderr)
            print('Install it with `cargo-build-sbf --tools-version v1.44` and rerun.', file=sys.stderr)
            return 1
        print(f'v1.44 SDK verified ({args.sdk_check}, {total} entries)')

    bad = check_linux_libs(LINUX)
    if bad:
        print('tracked Linux v1.44 sbpf target libraries do not match the manifest: ' + ', '.join(bad), file=sys.stderr)
        return 1
    print('Linux v1.44 sbpf target libraries verified (25 rlibs)')

    if hybrid_ok():
        print(f'hybrid144 already assembled at {HYBRID}')
    else:
        HYBRID.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['bash', str(HARNESS / 'make_hybrid144.sh'), str(HYBRID), str(SDK / 'rust'), str(LINUX), str(MANIFEST)], check=True)
        # The official archive ships an empty lib/self-contained directory, which git cannot track.
        (HYBRID / 'rust/lib/rustlib/sbpf-solana-solana/lib/self-contained').mkdir(exist_ok=True)
        if not hybrid_ok():
            print('hybrid144 assembly did not verify', file=sys.stderr)
            return 1
        print(f'hybrid144 assembled at {HYBRID}')
    sysroot = subprocess.check_output([str(HYBRID / 'rust/bin/rustc'), '--print', 'sysroot'], text=True).strip()
    assert Path(sysroot).resolve() == (HYBRID / 'rust').resolve(), sysroot

    (HOME_CACHE / 'locks').mkdir(parents=True, exist_ok=True)

    template = HOME_CACHE / 'template-target-sbpf'
    if args.warm and not template.exists():
        sys.path.insert(0, str(HARNESS))
        import fastbuild
        work = HOME_CACHE / 'warm'
        result = fastbuild.build(REPO / 'programs/pump', work, work / 'out', recipe='identity')
        print(json.dumps(result, indent=2))
        if not result['ok']:
            return 1
        shutil.rmtree(template, ignore_errors=True)
        subprocess.run(['cp', '-cRp', str(work / 'target-identity'), str(template)], check=True)
        print(f'dependency cache seeded at {template}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
