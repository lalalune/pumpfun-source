#!/usr/bin/env python3
"""Experiment-only builder (w8-toolchain-version): fastbuild staging with an alternative rustc
(--rustc PATH, e.g. a hybrid of another platform-tools release) and/or a host-triple `-vV` shim
(--fake-host TRIPLE). Never a proposal recipe by itself.
"""
import argparse, os, sys, subprocess, shutil, tomllib, json, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'harness'))
import fastbuild as F
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--fake-host'); ap.add_argument('--rustc', type=Path)
ap.add_argument('--cargo', type=Path); ap.add_argument('--jobs', default='2'); ap.add_argument('--rustflags', default='-Zremap-cwd-prefix=')
ap.add_argument('--triple', default='sbpf-solana-solana')
a = ap.parse_args()
triple = a.triple
work = a.work.resolve(); out = a.out.resolve(); work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
ws = work / 'ws'; crate = F.stage(a.src.resolve(), ws)
real = (a.rustc or F.RECIPES['identity']['rustc']).resolve()
env = os.environ.copy(); env.pop('CARGO_BUILD_TARGET_DIR', None); reg = Path.home() / '.cargo'
rustc = str(real)
if a.fake_host:
    rustc = str(HERE / 'rustc-hostvv'); env['FAKE_HOST'] = a.fake_host; env['REAL_RUSTC'] = str(real)
target = work / 'target'
env.update(RUSTC_WRAPPER=str(F.H / 'pump_physical_source_wrapper.py'), PUMP_LOGICAL_REGISTRY_SRC=str(reg / 'registry/src'), CARGO_HOME=str(reg),
           CARGO_TARGET_DIR=str(target), CARGO_BUILD_JOBS=a.jobs, RUSTC=rustc,
           CC=str(F.SDK / 'llvm/bin/clang'), AR=str(F.SDK / 'llvm/bin/llvm-ar'), OBJDUMP=str(F.SDK / 'llvm/bin/llvm-objdump'), OBJCOPY=str(F.SDK / 'llvm/bin/llvm-objcopy'))
env['CARGO_TARGET_' + triple.upper().replace('-', '_') + '_RUSTFLAGS'] = a.rustflags
env.pop('RUSTFLAGS', None); env.pop('CARGO_ENCODED_RUSTFLAGS', None)
for name in {'pump-recovered'} | F.local_packages(crate):
    for fp in list(target.glob(f'*/release/.fingerprint/{name}-*')): shutil.rmtree(fp, ignore_errors=True)
for so in target.glob('*/release/pump_recovered.so'): so.unlink()
cargo = str(a.cargo or (F.SDK / 'rust/bin/cargo'))
cmd = [cargo, 'build', '--manifest-path', str(crate / 'Cargo.toml'), '--release', '--target', triple, '--locked', '--offline']
slot = F.acquire_slot(); t0 = time.time()
try: r = subprocess.run(cmd, cwd=ws, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
finally: slot.close()
(out / 'build.log').write_text(r.stdout)
if r.returncode: print(r.stdout[-4000:]); sys.exit(1)
if any('exceeded max offset' in l for l in r.stdout.splitlines()): print('STACK WARNINGS present')
built = target / triple / 'release/pump_recovered.so'; shutil.copy2(built, out / 'unstripped.so')
print(json.dumps({'ok': True, 'seconds': round(time.time() - t0, 1), 'sha256': F.sha(out / 'unstripped.so')}))
