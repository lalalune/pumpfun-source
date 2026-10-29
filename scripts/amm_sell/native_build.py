#!/usr/bin/env python3
"""Fast, lane-isolated native macOS build of the maintained AMM for sell iteration.

Compiler: official macOS (aarch64) platform-tools v1.44 with the Linux v1.44
sbpf-solana-solana target libraries overlaid (the original links Linux-built std).
Recipe: the qualified layout-closure workspace transform, -Zremap-cwd-prefix=,
--locked --offline, and the disclosed ordered.ld linker script for the root crate
only. Only llvm-objcopy --strip-all touches the output.

Each lane owns LANE/ws (staged workspace), LANE/target and LANE/out/<id>.
A lane is seeded once (staged from --source-root, target cloned from a warm seed
when available) and then rebuilt any number of times; only the two local crates
recompile.

Examples:
  native_build.py --lane LANES/a --source-root /path/to/repo --id baseline
  native_build.py --lane LANES/a --sell candidate_sell.rs --id try-17
  native_build.py --lane LANES/a --patch change.patch --id try-18   (patch vs lane ws)
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SWARM = Path(os.environ.get('AMM_SELL_SWARM', HERE.parent)).resolve()
SDK = SWARM / 'infra/sdk-native'
CARGO_HOME = SWARM / 'infra/cargo-home'
SEED_TARGET = SWARM / 'baselines/warm-target'
PRISTINE = SWARM / 'baselines/pristine-ws'
SELL_REL = 'programs/pump-amm/src/instructions/swap/sell.rs'
PROGRAM = 'pump_amm_recovered.so'

_spec = importlib.util.spec_from_file_location('amm_workspace_recipe', HERE / 'workspace_recipe.py')
recipe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recipe)

RUSTC_WRAPPER = '''#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path
compiler, *arguments = sys.argv[1:]
environment = os.environ.copy()
out = Path(environment['AMM_LANE_OUT'])
if '--target' in arguments and '--crate-name' in arguments and any(a.startswith('metadata=') for a in arguments):
    # Cargo's -C metadata hashes the host rustc's verbose version. Restore the
    # Linux-host values so symbol/CGU hashes equal the qualified Linux build.
    name = arguments[arguments.index('--crate-name') + 1]
    source = next(a for a in arguments if a.endswith('.rs'))
    match = re.search(r'/registry/src/[^/]+/([^/]+)/', source)
    package = match.group(1) if match else source
    types = [arguments[i + 1] for i, a in enumerate(arguments) if a == '--crate-type']
    features = sorted(arguments[i + 1] for i, a in enumerate(arguments) if a == '--cfg' and arguments[i + 1].startswith('feature='))
    table = json.loads(Path(environment['AMM_METADATA_MAP']).read_text())
    hits = [r for r in table if r['crate'] == name and r['package'] == package and r['types'] == types and r['features'] == features]
    if len(hits) != 1:
        raise SystemExit('No unique Linux metadata for ' + repr((name, package, types, features)))
    for i, a in enumerate(arguments):
        if i and arguments[i - 1] == '-C' and a.startswith('metadata='):
            if a != 'metadata=' + hits[0]['mac_metadata']:
                raise SystemExit('Unexpected native metadata for ' + name + ': ' + a)
            arguments[i] = 'metadata=' + hits[0]['linux_metadata']
if '--crate-name' in arguments and arguments[arguments.index('--crate-name') + 1] == 'pump_amm_recovered':
    original = list(arguments)
    environment['AMM_LAYOUT_REAL_LLD'] = str(Path(compiler).parent.parent / 'lib/rustlib/aarch64-apple-darwin/bin/rust-lld')
    arguments += ['-C', 'linker=' + str(Path(environment['AMM_LANE_HARNESS']) / 'linker_wrapper.py')]
    extra = environment.get('AMM_EXTRA_ROOT_RUSTFLAGS', '').split()
    arguments += extra
    (out / 'root-rustc-invocation.json').write_text(json.dumps({
        'compiler': compiler, 'original_arguments': original, 'effective_arguments': arguments,
        'extra_root_flags': extra}, indent=2) + '\\n')
os.execvpe(compiler, [compiler, *arguments], environment)
'''

LINKER_WRAPPER = '''#!/usr/bin/env python3
import hashlib, json, os, sys
from pathlib import Path
original = sys.argv[1:]
arguments = list(original)
if arguments.count('--script') != 1:
    raise SystemExit('Expected exactly one built-in link script')
index = arguments.index('--script') + 1
default = Path(arguments[index])
digest = hashlib.sha256(default.read_bytes()).hexdigest()
if digest != '5e8370b9380f55411d827721e2e43c8cfd1eac71d1383e20b938397bc0bd82c3':
    raise SystemExit('Built-in link script changed: ' + digest)
out = Path(os.environ['AMM_LANE_OUT'])
script = os.environ.get('AMM_LINK_SCRIPT') or str(Path(os.environ['AMM_LANE_HARNESS']) / 'ordered-native.ld')
arguments[index] = script
arguments += ['--Map=' + str(out / 'link.map')]
(out / 'linker-invocation.json').write_text(json.dumps({'original_arguments': original,
    'effective_arguments': arguments, 'script': script}, indent=2) + '\\n')
linker = os.environ['AMM_LAYOUT_REAL_LLD']
os.execv(linker, [linker, *arguments])
'''


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def native_link_script():
    """ordered.ld with Linux-host archive hashes (-C extra-filename) translated to this host's."""
    text = (HERE / 'ordered.ld').read_text()
    for row in json.loads((HERE / 'metadata-map.json').read_text()):
        if row['linux_extra'] and row['mac_extra']:
            text = text.replace(row['linux_extra'], row['mac_extra'])
    return text.encode()


def ensure_lane(lane, source_root):
    ws = lane / 'ws'
    harness = lane / 'harness'
    lane.mkdir(parents=True, exist_ok=True)
    if not ws.exists():
        if source_root is not None:
            recipe.stage(Path(source_root), ws)
        elif PRISTINE.exists():
            subprocess.run(['cp', '-R', str(PRISTINE), str(ws)], check=True)
        else:
            raise SystemExit('New lane needs --source-root (a repo-like tree with programs/pump-amm and crates/native-transfer-fee)')
    harness.mkdir(parents=True, exist_ok=True)
    for name, text in (('rustc_wrapper.py', RUSTC_WRAPPER), ('linker_wrapper.py', LINKER_WRAPPER)):
        path = harness / name
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
            path.chmod(0o755)
    native_script = native_link_script()
    for name, data in (('ordered-native.ld', native_script), ('metadata-map.json', (HERE / 'metadata-map.json').read_bytes())):
        if not (harness / name).exists() or (harness / name).read_bytes() != data:
            (harness / name).write_bytes(data)
    target = lane / 'target'
    if not target.exists():
        if SEED_TARGET.exists():
            # APFS clone: instant, copy-on-write.
            subprocess.run(['cp', '-c', '-R', str(SEED_TARGET), str(target)], check=True)
        else:
            target.mkdir(parents=True)
    return ws, harness, target


def build(lane, build_id, source_root=None, sell=None, patch=None, extra_root_flags='', link_script=None,
          keep_ws=False, jobs=4):
    lane = Path(lane).absolute()
    ws, harness, target = ensure_lane(lane, source_root)
    out = lane / 'out' / build_id
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if PRISTINE.exists():
        # Every attempt starts from the canonical inputs: earlier patches never leak.
        subprocess.run(['rsync', '-a', '--delete', '--checksum', '--exclude', 'target',
                        str(PRISTINE) + '/', str(ws) + '/'], check=True)
    sell_path = ws / SELL_REL
    if sell is not None:
        shutil.copyfile(sell, sell_path)
    if patch is not None:
        subprocess.run(['patch', '-p1', '-d', str(ws), '-i', str(Path(patch).absolute())], check=True,
                       stdout=subprocess.DEVNULL)
    shutil.copyfile(sell_path, out / 'sell.rs')
    # Restored files can carry old mtimes; force both local crates to recompile.
    now = time.time()
    for crate in ('programs/pump-amm', 'crates/native-transfer-fee'):
        for path in (ws / crate).rglob('*.rs'):
            os.utime(path, (now, now))
    env = {k: v for k, v in os.environ.items() if k not in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WORKSPACE_WRAPPER')}
    env.update({
        'CARGO_HOME': str(CARGO_HOME), 'CARGO_TARGET_DIR': str(target),
        'RUSTC': str(SDK / 'rust/bin/rustc'), 'RUSTDOC': str(SDK / 'rust/bin/rustdoc'),
        'CC': str(SDK / 'llvm/bin/clang'), 'AR': str(SDK / 'llvm/bin/llvm-ar'),
        'CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS': ' -Zremap-cwd-prefix=',
        'CARGO_BUILD_JOBS': str(jobs), 'RUSTC_WRAPPER': str(harness / 'rustc_wrapper.py'),
        'AMM_LANE_OUT': str(out), 'AMM_LANE_HARNESS': str(harness),
        'AMM_EXTRA_ROOT_RUSTFLAGS': extra_root_flags,
        'AMM_METADATA_MAP': str(harness / 'metadata-map.json'),
    })
    if link_script:
        env['AMM_LINK_SCRIPT'] = str(Path(link_script).absolute())
    else:
        env.pop('AMM_LINK_SCRIPT', None)
    started = time.time()
    with (out / 'build.log').open('wb') as log:
        result = subprocess.run([str(SDK / 'rust/bin/cargo'), 'build', '--release', '--target', 'sbpf-solana-solana',
                                 '--manifest-path', str(ws / 'Cargo.toml'), '--locked', '--offline', '--verbose'],
                                cwd=ws, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = {'lane': str(lane), 'id': build_id, 'returncode': result.returncode,
              'seconds': round(time.time() - started, 1), 'sell_sha256': sha(out / 'sell.rs'),
              'extra_root_flags': extra_root_flags, 'link_script': link_script}
    if result.returncode == 0:
        unstripped = target / 'sbpf-solana-solana/release' / PROGRAM
        shutil.copyfile(unstripped, out / 'symbols.so')
        subprocess.run([str(SDK / 'llvm/bin/llvm-objcopy'), '--strip-all', str(out / 'symbols.so'),
                        str(out / 'candidate.so')], check=True)
        record['candidate_sha256'] = sha(out / 'candidate.so')
        record['symbols_sha256'] = sha(out / 'symbols.so')
    (out / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--lane', required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--source-root')
    parser.add_argument('--sell', help='replacement sell.rs to copy into the lane workspace before building')
    parser.add_argument('--patch', help='unified diff (-p1, relative to the workspace root) applied before building')
    parser.add_argument('--extra-root-flags', default='', help='extra rustc flags for the root crate only (diagnostic)')
    parser.add_argument('--link-script', help='alternate linker script (diagnostic)')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    record = build(args.lane, args.id, args.source_root, args.sell, args.patch, args.extra_root_flags,
                   args.link_script, jobs=args.jobs)
    print(json.dumps(record))
    sys.exit(0 if record['returncode'] == 0 else 1)


if __name__ == '__main__':
    main()
