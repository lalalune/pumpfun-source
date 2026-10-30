#!/usr/bin/env python3
"""Prepare the main-Pump reconstruction toolchain on this machine (macOS arm64, Linux x86_64).

  python3 reconstruction/toolchain/bootstrap.py [--sdk-check full|quick|skip] [--warm]

1. Verifies ~/.cache/solana/v1.44/platform-tools against v1.44-macos-inventory.json
   (every listed file hash by default, and the exact file/symlink set) on macOS. On
   Linux x86_64 the same directory holds the official platform-tools-linux-x86_64
   v1.44 archive; no inventory describes that host build, so check_sdk_linux()
   identifies it by the compiler revision and the pinned target libraries instead.
   The SDK itself is not stored in git: its
   librustc_driver is 134 MB, above GitHub's 100 MB file limit. Install it with
   `cargo-build-sbf --tools-version v1.44` (or extract the official v1.44
   platform-tools-osx-aarch64 / platform-tools-linux-x86_64 release there), then
   rerun this script.
2. Verifies the official Linux x86_64 v1.44 sbpf-solana-solana target libraries
   tracked in linux-v1.44-x86_64/ against harness/linux144-sbpf-target-libs.sha256.
3. Assembles the identity toolchain into $PUMP_RECON_HOME/toolchains/hybrid144
   (default ~/.cache/pumpfun-reconstruction): on macOS the macOS v1.44 rustc with
   the Linux v1.44 sbpf target libraries, via harness/make_hybrid144.sh; on Linux
   x86_64 the platform's own v1.44 rustc with those same tracked target libraries,
   which are the compiler inputs that decide the emitted code.
4. Creates the shared build-slot lock directory used by harness/fastbuild.py.
5. With --warm, builds programs/pump once and keeps its dependency artifacts as
   $PUMP_RECON_HOME/template-target-sbpf so later builds only recompile the
   pump crate.

Nothing is downloaded and nothing outside $PUMP_RECON_HOME is written, except
the --warm build's own work directory under $PUMP_RECON_HOME.
"""
import argparse
import fcntl
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECON = HERE.parent
REPO = RECON.parent
HARNESS = RECON / 'harness'
# Share the builder's invocation-relative cache, preserving symlink spelling.
HOME_CACHE = Path(os.environ.get('PUMP_RECON_HOME', Path.home() / '.cache/pumpfun-reconstruction')).absolute()
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
LINUX = HERE / 'linux-v1.44-x86_64'
MANIFEST = HARNESS / 'linux144-sbpf-target-libs.sha256'
HYBRID = HOME_CACHE / 'toolchains/hybrid144'
HOST_PLATFORM = sys.platform
HOST_MACHINE = platform.machine()
# The only Linux host build the repository pins is the official
# platform-tools-linux-x86_64 v1.44 archive.
LINUX_HOST_TRIPLE = 'x86_64-unknown-linux-gnu'
# anza rust revision both v1.44 host builds were produced from.
SDK_REVISION = '08b7341888ab480dfaaa0698300cbbbbb2d75b53'
# APFS clonefile (-c) keeps the published warm cache cheap on macOS; GNU cp rejects -c.
CLONE = ['cp', '-cRp'] if HOST_PLATFORM == 'darwin' else ['cp', '-a']


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
    # The hybrid toolchain links the SDK host rustlib directory. An unlisted
    # file there can therefore become a compiler input despite every listed
    # digest matching. Treat the inventory as an exact file/symlink set.
    actual = set()
    def scan_error(error):
        problems.append(f'SDK traversal: {error}')
    for directory, directories, files in os.walk(SDK, onerror=scan_error, followlinks=False):
        base = Path(directory)
        actual.update((base / name).relative_to(SDK).as_posix() for name in files)
        # os.walk lists symlinked directories separately and never descends into
        # them with followlinks=False; they are still inventoried inputs.
        actual.update((base / name).relative_to(SDK).as_posix() for name in directories
                      if (base / name).is_symlink())
    problems.extend(f'unexpected SDK input: {rel}' for rel in sorted(actual - inventory.keys()))
    return len(inventory), problems


def check_sdk_linux(mode):
    """Validate an official Linux x86_64 v1.44 platform-tools extraction.

    v1.44-macos-inventory.json describes the macOS host build and cannot certify
    this archive, so the identity inputs are checked directly: the compiler
    revision the release was produced from, the host rustlib the compiler links
    against, and the sbpf-solana-solana target libraries that decide the emitted
    code.
    """
    problems = []
    rustc = SDK / 'rust/bin/rustc'
    if rustc.is_symlink() or not rustc.is_file():
        problems.append('missing rust/bin/rustc')
    if not (SDK / 'rust/lib/rustlib' / LINUX_HOST_TRIPLE).is_dir():
        problems.append(f'missing rust/lib/rustlib/{LINUX_HOST_TRIPLE}')
    version = SDK / 'version.md'
    if not version.is_file():
        problems.append('missing version.md')
    elif (version.read_text(encoding='utf-8').splitlines() or [''])[0].split()[:1] != [SDK_REVISION]:
        problems.append(f'rust revision is not {SDK_REVISION}')
    if not (SDK / 'rust/lib/rustlib/sbpf-solana-solana/lib').is_dir():
        problems.append('missing rust/lib/rustlib/sbpf-solana-solana/lib')
    elif mode == 'full':
        problems.extend('SDK ' + problem for problem in check_linux_libs(SDK))
    return problems


def assemble_linux():
    """Assemble the identity toolchain from the Linux v1.44 SDK.

    The identity inputs are the v1.44 compiler for this host and the official
    Linux sbpf-solana-solana target libraries. Both belong to the same archive, so
    unlike the macOS hybrid no cross-host borrowing is needed; the target
    libraries are published from the tracked, manifest-pinned copy.
    """
    HYBRID.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=HYBRID.name + '.stage.', dir=HYBRID.parent))
    try:
        (stage / 'rust/bin').mkdir(parents=True)
        (stage / 'rust/lib/rustlib').mkdir(parents=True)
        shutil.copy2(SDK / 'rust/bin/rustc', stage / 'rust/bin/rustc')
        for library in sorted((SDK / 'rust/lib').glob('lib*.so')):
            shutil.copy2(library, stage / 'rust/lib' / library.name)
        # rustc derives its default sysroot from the location of librustc_driver,
        # which lives in rust/lib, so <toolchain>/rust is the sysroot without
        # any --sysroot or RUSTFLAGS change.
        (stage / 'rust/lib/rustlib' / LINUX_HOST_TRIPLE).symlink_to(
            SDK / 'rust/lib/rustlib' / LINUX_HOST_TRIPLE)
        shutil.copytree(LINUX / 'rust/lib/rustlib/sbpf-solana-solana',
                        stage / 'rust/lib/rustlib/sbpf-solana-solana')
        # The official archive ships an empty lib/self-contained directory, which git cannot track.
        (stage / 'rust/lib/rustlib/sbpf-solana-solana/lib/self-contained').mkdir(exist_ok=True)
        shutil.copy2(SDK / 'version.md', stage / 'version.md')
        if HYBRID.exists() or HYBRID.is_symlink():
            backup = Path(tempfile.mkdtemp(prefix=HYBRID.name + '.backup.', dir=HYBRID.parent))
            backup.rmdir()
            HYBRID.rename(backup)
            stage.rename(HYBRID)
            shutil.rmtree(backup, ignore_errors=True)
        else:
            stage.rename(HYBRID)
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def hybrid_ok_linux():
    rust = HYBRID / 'rust'
    rustc = rust / 'bin/rustc'
    if not rustc.is_file() or sha(rustc) != sha(SDK / 'rust/bin/rustc'):
        return False
    # The compiler also loads the host shared libraries copied by assemble_linux().
    # Reuse requires the same complete set and bytes, not just an unchanged rustc.
    expected = {path.name: path for path in (SDK / 'rust/lib').glob('lib*.so')}
    copied = {path.name: path for path in (rust / 'lib').glob('lib*.so')}
    if not expected or copied.keys() != expected.keys():
        return False
    if any(path.is_symlink() or not path.is_file() or sha(path) != sha(expected[name])
           for name, path in copied.items()):
        return False
    host = rust / 'lib/rustlib' / LINUX_HOST_TRIPLE
    if not host.is_symlink() or host.resolve() != (SDK / 'rust/lib/rustlib' / LINUX_HOST_TRIPLE).resolve():
        return False
    return not check_linux_libs(HYBRID)


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


def publish_dependency_cache(source, template):
    """Expose a cache only after copying finishes; serialize competing publishers."""
    template.parent.mkdir(parents=True, exist_ok=True)
    with (template.parent / (template.name + '.lock')).open('a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if template.exists() or template.is_symlink():
            return False
        with tempfile.TemporaryDirectory(prefix=template.name + '.stage.', dir=template.parent) as temporary:
            staged = Path(temporary) / 'target'
            subprocess.run(CLONE + [str(source), str(staged)], check=True)
            if not staged.is_dir() or staged.is_symlink():
                raise RuntimeError('dependency cache source must be a directory')
            staged.rename(template)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sdk-check', choices=['full', 'quick', 'skip'], default='full')
    ap.add_argument('--warm', action='store_true', help='build programs/pump once to seed the shared dependency cache')
    args = ap.parse_args()

    if HOST_PLATFORM not in ('darwin', 'linux'):
        print(f'unsupported host {HOST_PLATFORM}: the v1.44 identity toolchain is assembled for '
              'macOS arm64 and Linux x86_64', file=sys.stderr)
        return 1

    linux_host = HOST_PLATFORM == 'linux'
    if linux_host and HOST_MACHINE != 'x86_64':
        print(f'unsupported Linux machine {HOST_MACHINE}: only the x86_64 platform-tools archive is pinned',
              file=sys.stderr)
        return 1

    if args.sdk_check != 'skip':
        if linux_host:
            problems = check_sdk_linux(args.sdk_check)
            if problems:
                print(f'v1.44 SDK at {SDK} is not the pinned Linux platform-tools release:', file=sys.stderr)
                print('  ' + '\n  '.join(problems[:20]), file=sys.stderr)
                print('Extract the official platform-tools-linux-x86_64 v1.44 release there and rerun.',
                      file=sys.stderr)
                return 1
            print(f'Linux v1.44 SDK verified ({args.sdk_check})')
        else:
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

    if linux_host:
        if hybrid_ok_linux():
            print(f'identity toolchain already assembled at {HYBRID}')
        else:
            assemble_linux()
            if not hybrid_ok_linux():
                print('identity toolchain assembly did not verify', file=sys.stderr)
                return 1
            print(f'identity toolchain assembled at {HYBRID}')
    elif hybrid_ok():
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
        if publish_dependency_cache(work / 'target-identity', template):
            print(f'dependency cache seeded at {template}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
