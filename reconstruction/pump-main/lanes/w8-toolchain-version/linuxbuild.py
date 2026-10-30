#!/usr/bin/env python3
"""Experiment builder: the *complete* official Linux x86_64 platform-tools v1.44 (cargo + rustc +
LLVM + sysroot) running natively for linux/amd64 under podman, on the same staged workspace that
fastbuild.py builds. This tests the "the original was built on a Linux host" hypothesis without any
shim: cargo's `rustc -vV` host, proc-macro/build-script hosts and the compiler binary are all Linux.

usage: linuxbuild.py --src <crate> --work <dir> --out <dir> --toolchain <extracted linux platform-tools>
       [--image IMAGE] [--rustflags '-Zremap-cwd-prefix='] [--jobs N] [--target-env-name sbpf|sbf]

Holds two of the shared PUMP_BUILD_SLOTS while the container compiles.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[3] / 'harness'
sys.path.insert(0, str(HARNESS))
import fastbuild  # noqa: E402

PT = '/root/.cache/solana/v1.44/platform-tools'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', type=Path, required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--toolchain', type=Path, required=True)
    ap.add_argument('--image', default='localhost/pump-v144-linux-host-control-20261028')
    ap.add_argument('--rustflags', default='-Zremap-cwd-prefix=')
    ap.add_argument('--jobs', default='4')
    ap.add_argument('--triple', default='sbpf-solana-solana')
    ap.add_argument('--keep-target', action='store_true')
    ap.add_argument('--platform', default='linux/amd64')
    a = ap.parse_args()
    src, work, out = a.src.resolve(), a.work.resolve(), a.out.resolve()
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    ws = work / 'ws'
    fastbuild.stage(src, ws)
    target = work / 'target-linux'
    if not a.keep_target:
        for fp in list(target.glob('*/release/.fingerprint/pump-*')) + list(target.glob('*/release/.fingerprint/pump_*')):
            shutil.rmtree(fp, ignore_errors=True)
        for so in target.glob('*/release/*.so'):
            so.unlink()
    target.mkdir(exist_ok=True)
    tenv = 'CARGO_TARGET_' + a.triple.upper().replace('-', '_') + '_RUSTFLAGS'
    cmd = ['podman', 'run', '--rm', '--platform', a.platform, '--network', 'none',
           '-v', f'{a.toolchain.resolve()}:{PT}:ro',
           '-v', f'{Path.home() / ".cargo/registry"}:/root/.cargo/registry:ro',
           '-v', f'{ws}:/work/ws', '-v', f'{target}:/work/target',
           '-w', '/work/ws',
           '-e', 'CARGO_HOME=/root/.cargo', '-e', 'CARGO_TARGET_DIR=/work/target',
           '-e', f'CARGO_BUILD_JOBS={a.jobs}', '-e', f'RUSTC={PT}/rust/bin/rustc',
           '-e', f'CC={PT}/llvm/bin/clang', '-e', f'AR={PT}/llvm/bin/llvm-ar',
           '-e', f'OBJDUMP={PT}/llvm/bin/llvm-objdump', '-e', f'OBJCOPY={PT}/llvm/bin/llvm-objcopy',
           '-e', f'{tenv}={a.rustflags}',
           a.image, f'{PT}/rust/bin/cargo', 'build', '--manifest-path', 'programs/pump/Cargo.toml',
           '--release', '--target', a.triple, '--locked', '--offline']
    s1 = fastbuild.acquire_slot(); s2 = fastbuild.acquire_slot()
    t0 = time.time()
    try:
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    finally:
        s1.close(); s2.close()
    (out / 'build.log').write_text(r.stdout)
    (out / 'command.json').write_text(json.dumps(cmd, indent=1) + '\n')
    if r.returncode:
        sys.stdout.write(r.stdout[-5000:]); sys.exit(1)
    built = target / a.triple / 'release/pump_recovered.so'
    shutil.copy2(built, out / 'unstripped.so')
    subprocess.run([str(fastbuild.SDK / 'llvm/bin/llvm-objcopy'), '--strip-all', str(built), str(out / 'candidate.so')], check=True)
    print(json.dumps({'ok': True, 'seconds': round(time.time() - t0, 1), 'unstripped_sha256': sha(out / 'unstripped.so'),
                      'candidate_sha256': sha(out / 'candidate.so')}, indent=1))


if __name__ == '__main__':
    main()
