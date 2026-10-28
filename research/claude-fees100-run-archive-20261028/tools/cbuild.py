#!/usr/bin/env python3
"""Canonical Linux v1.44 Fees build (the frontier's recipe) in container claude-fees100-build.

usage: python3 -I cbuild.py SRC_DIR OUT_PREFIX [extra rustc args...]
SRC_DIR must contain Cargo.toml, Cargo.lock, programs/, pump-fees-math/ and ordered.ld (the layout recipe).
The tree is copied to RR/cwork/src/<label> (container /work/src/<label>), built with cargo rustc
--release --target sbpf-solana-solana --locked --offline, linked through a wrapper that swaps the SDK
linker script for ordered.ld, then stripped with the pinned v1.52 llvm-objcopy.
The vendored macro must sit at /work/next637/vendor/used-public: Cargo hashes the out-of-workspace path
(relative to the workspace) into every crate metadata hash, and ordered.ld selects sections by those hashes.
Cargo does not track the linker script, so the root crate is always recompiled and relinked.
Writes OUT_PREFIX-{symbols.so,candidate.so,build.log,launch.json,result.json,map}. 2 container slots.
"""
from pathlib import Path
import fcntl, hashlib, json, re, shutil, subprocess, sys, time
RR = Path('/Users/shawwalters/fees100-run')
CW = RR / 'cwork'
CONTAINER = 'claude-fees100-build'
STRIP = '/Users/shawwalters/.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objcopy'
sha = lambda b: hashlib.sha256(b).hexdigest()

def acquire(slots=2):
    lockdir = Path(__file__).resolve().parent / 'locks'; lockdir.mkdir(exist_ok=True)
    while True:
        for i in range(slots):
            f = open(lockdir / f'container{i}.lock', 'w')
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); return i, f
            except BlockingIOError:
                f.close()
        time.sleep(5)

def main():
    src = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve(); extra = sys.argv[3:]
    out.parent.mkdir(parents=True, exist_ok=True)
    label = out.name + '-' + sha(str(out).encode())[:8]
    dest = CW / 'src' / label
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=False, ignore=shutil.ignore_patterns('target', '*.so'))
    toml = (dest / 'Cargo.toml').read_text()
    toml = re.sub(r'anchor-attribute-program = \{ path = "[^"]+" \}',
                  'anchor-attribute-program = { path = "/work/next637/vendor/used-public" }', toml)
    (dest / 'Cargo.toml').write_text(toml)
    assert (dest / 'ordered.ld').is_file(), 'SRC_DIR needs ordered.ld (layout recipe)'
    cw = '/work/src/' + label
    (dest / 'linker.sh').write_text(f'''#!/bin/bash
set -e
args=("$@")
for ((i=0; i<${{#args[@]}}; i++)); do
  if [[ "${{args[i]}}" == "-T" || "${{args[i]}}" == "--script" ]]; then
    args[i+1]={cw}/ordered.ld
  elif [[ "${{args[i]}}" == --script=* ]]; then
    args[i]=--script={cw}/ordered.ld
  fi
done
printf '%s\\n' "${{args[@]}}" > {cw}/effective-link-args.txt
exec /work/sdk/rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld "${{args[@]}}"
''')
    (dest / 'linker.sh').chmod(0o755)
    slot, fh = acquire()
    target = f'/work/targets/slot{slot}'
    env = {'PATH': '/work/sdk/rust/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
           'RUSTC': '/work/sdk/rust/bin/rustc', 'CC': '/work/sdk/llvm/bin/clang', 'AR': '/work/sdk/llvm/bin/llvm-ar',
           'CARGO_HOME': '/cargo', 'CARGO_TARGET_DIR': target, 'CARGO_BUILD_JOBS': '2',
           'CARGO_NET_OFFLINE': 'true', 'RUSTFLAGS': '-Zremap-cwd-prefix='}
    cmd = ['podman', 'exec']
    for k, v in env.items(): cmd += ['-e', f'{k}={v}']
    cmd += ['-w', cw, CONTAINER, '/work/sdk/rust/bin/cargo', 'rustc', '--verbose', '--manifest-path',
            cw + '/programs/pump-fees/Cargo.toml', '--release', '--target', 'sbpf-solana-solana', '--locked',
            '--offline', '--jobs', '2', '--lib', '--',
            f'--remap-path-prefix={cw}/programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/',
            f'--remap-path-prefix={cw}/pump-fees-math/=pump-fees-math/',
            '--remap-path-prefix=programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/',
            '-C', f'link-arg=-Map={cw}/link.map', '-C', f'linker={cw}/linker.sh'] + extra
    Path(str(out) + '-launch.json').write_text(json.dumps({'command': cmd, 'slot': slot, 'src': str(src)}, indent=1) + '\n')
    rel = CW / 'targets' / f'slot{slot}' / 'sbpf-solana-solana/release'
    so = rel / 'pump_fees_candidate.so'
    if so.exists(): so.unlink()
    # deleting the outputs (not the fingerprint dirs, which Cargo expects to exist) makes the unit dirty
    for p in list((rel / 'deps').glob('pump_fees_candidate*')) + list((rel / 'deps').glob('libpump_fees_candidate*')):
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    start = time.monotonic()
    with open(str(out) + '-build.log', 'wb') as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    res = {'exit_code': r.returncode, 'elapsed_seconds': round(time.monotonic() - start, 1), 'slot': slot}
    if r.returncode == 0 and so.exists():
        sym = Path(str(out) + '-symbols.so'); cand = Path(str(out) + '-candidate.so')
        shutil.copyfile(so, sym)
        subprocess.run([STRIP, '--strip-all', str(sym), str(cand)], check=True)
        if (dest / 'link.map').exists(): shutil.copyfile(dest / 'link.map', str(out) + '.map')
        res.update(symbols_sha256=sha(sym.read_bytes()), candidate_sha256=sha(cand.read_bytes()))
    Path(str(out) + '-result.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res)); fh.close()
    return r.returncode

if __name__ == '__main__':
    sys.exit(main())
