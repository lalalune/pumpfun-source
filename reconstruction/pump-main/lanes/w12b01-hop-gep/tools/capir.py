#!/usr/bin/env python3
"""Scratch-only: build crate copy with --emit=link,llvm-ir[,mir]; copy module .ll (and .mir) to OUT.
--extra '-Cno-prepopulate-passes' gives the pre-opt module instead (the .so is then junk)."""
import argparse, json, sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))  # reconstruction/harness
import fastbuild
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--extra', default='')
ap.add_argument('--mir', action='store_true')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
emit = 'link,llvm-ir' + (',mir' if a.mir else '')
extra = ['--emit=' + emit, '-Zfewer-names=no'] + a.extra.split()
real = fastbuild.run_compiler
def run(cmd, *ra, **kw):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
fastbuild.run_compiler = run
for m in a.work.rglob('pump_recovered*.ll'): m.unlink()
for m in a.work.rglob('pump_recovered*.mir'): m.unlink()
res = fastbuild.build(a.src, a.work, a.out, quiet=True)
for m in a.work.rglob('pump_recovered*.ll'):
    shutil.move(str(m), a.out / 'module.ll'); break
for m in a.work.rglob('pump_recovered*.mir'):
    shutil.move(str(m), a.out / 'module.mir'); break
print(json.dumps({k: res.get(k) for k in ('ok', 'unstripped_sha256', 'seconds', 'log')}))
