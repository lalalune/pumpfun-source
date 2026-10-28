#!/usr/bin/env python3
"""layout-elf lane: cbuild.py-identical Linux v1.44 container build that ALSO keeps the link inputs.

usage: python3 -I lbuild.py SRC_DIR OUT_PREFIX [--ld ORDERED_LD] [extra rustc args...]

Same environment, flags, container, slot locks and vendored-macro path as R/shared/tools/cbuild.py
(so outputs are byte-identical to cbuild.py for the same inputs). Differences:
  * --ld PATH uses PATH as the layout recipe instead of SRC_DIR/ordered.ld;
  * the linker wrapper copies the root crate objects, rustc's symbols.o and version-script list into
    OUT_PREFIX-linkinputs/ (diagnostic relinks with relink.py) and saves the incoming/effective args.
Writes OUT_PREFIX-{symbols.so,candidate.so,build.log,launch.json,result.json,map,link-args.txt}.
"""
from pathlib import Path
import fcntl, hashlib, json, os, re, shutil, subprocess, sys, time
R = Path('/Users/shawwalters/fees100-run')
CW = R / 'cwork'
CONTAINER = 'claude-fees100-build'
STRIP = '/Users/shawwalters/.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objcopy'
LOCKDIR = R / 'shared/tools/locks'
sha = lambda b: hashlib.sha256(b).hexdigest()

def acquire(slots=2):
    LOCKDIR.mkdir(exist_ok=True)
    while True:
        for i in range(slots):
            f = open(LOCKDIR / f'container{i}.lock', 'w')
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); return i, f
            except BlockingIOError:
                f.close()
        time.sleep(5)

def main():
    argv = sys.argv[1:]
    ld = None
    if '--ld' in argv:
        i = argv.index('--ld'); ld = Path(argv[i + 1]).resolve(); del argv[i:i + 2]
    src = Path(argv[0]).resolve(); out = Path(argv[1]).resolve(); extra = argv[2:]
    out.parent.mkdir(parents=True, exist_ok=True)
    label = out.name + '-' + sha(str(out).encode())[:8]
    dest = CW / 'src' / label
    if dest.exists(): shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=False, ignore=shutil.ignore_patterns('target', '*.so'))
    toml = (dest / 'Cargo.toml').read_text()
    toml = re.sub(r'anchor-attribute-program = \{ path = "[^"]+" \}',
                  'anchor-attribute-program = { path = "/work/next637/vendor/used-public" }', toml)
    (dest / 'Cargo.toml').write_text(toml)
    if ld is not None:
        shutil.copyfile(ld, dest / 'ordered.ld')
    assert (dest / 'ordered.ld').is_file(), 'need ordered.ld (SRC_DIR/ordered.ld or --ld)'
    cw = '/work/src/' + label
    (dest / 'linker.sh').write_text(f'''#!/bin/bash
set -e
printf '%s\\n' "$@" > {cw}/incoming-link-args.txt
args=("$@")
mkdir -p {cw}/linkinputs
for ((i=0; i<${{#args[@]}}; i++)); do
  a="${{args[i]}}"
  if [[ "$a" == "-T" || "$a" == "--script" ]]; then
    cp "${{args[i+1]}}" {cw}/linkinputs/sdk-default.ld
    args[i+1]={cw}/ordered.ld
  elif [[ "$a" == --script=* ]]; then
    cp "${{a#--script=}}" {cw}/linkinputs/sdk-default.ld
    args[i]=--script={cw}/ordered.ld
  elif [[ "$a" == --version-script=* ]]; then
    cp "${{a#--version-script=}}" {cw}/linkinputs/version-script.list
  elif [[ "$a" == *.o && -f "$a" ]]; then
    cp "$a" {cw}/linkinputs/
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
    Path(str(out) + '-launch.json').write_text(json.dumps({'command': cmd, 'slot': slot, 'src': str(src),
        'ld': str(ld) if ld else None, 'ld_sha256': sha((dest / 'ordered.ld').read_bytes())}, indent=1) + '\n')
    so = CW / 'targets' / f'slot{slot}' / 'sbpf-solana-solana/release/pump_fees_candidate.so'
    if so.exists(): so.unlink()
    start = time.monotonic()
    with open(str(out) + '-build.log', 'wb') as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT)
    res = {'exit_code': r.returncode, 'elapsed_seconds': round(time.monotonic() - start, 1), 'slot': slot}
    if r.returncode == 0 and so.exists():
        sym = Path(str(out) + '-symbols.so'); cand = Path(str(out) + '-candidate.so')
        shutil.copyfile(so, sym)
        subprocess.run([STRIP, '--strip-all', str(sym), str(cand)], check=True)
        if (dest / 'link.map').exists(): shutil.copyfile(dest / 'link.map', str(out) + '.map')
        for n in ('effective-link-args.txt', 'incoming-link-args.txt'):
            if (dest / n).exists(): shutil.copyfile(dest / n, str(out) + '-' + n)
        li = Path(str(out) + '-linkinputs')
        if li.exists(): shutil.rmtree(li)
        if (dest / 'linkinputs').exists(): shutil.copytree(dest / 'linkinputs', li)
        shutil.copyfile(dest / 'ordered.ld', str(out) + '-ordered.ld')
        res.update(symbols_sha256=sha(sym.read_bytes()), candidate_sha256=sha(cand.read_bytes()))
    Path(str(out) + '-result.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res)); fh.close()
    return r.returncode

if __name__ == '__main__':
    sys.exit(main())
