#!/usr/bin/env python3
"""Scratch-only: build crate copy with extra --emit=llvm-ir; copy module .ll to OUT."""
import argparse, json, sys, shutil
from pathlib import Path
H = Path('./worktrees/w7r1-swaphop-regsched/reconstruction/harness')
sys.path.insert(0, str(H))
import fastbuild
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--extra', default='')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
extra = ['--emit=link,llvm-ir', '-Zfewer-names=no'] + a.extra.split()
real = fastbuild.run_compiler
def run(cmd, *ra, **kw):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
fastbuild.run_compiler = run
res = fastbuild.build(a.src, a.work, a.out)
for mod in (a.work / 'target-identity').glob('*/release/deps/pump_recovered*.ll'):
    shutil.copy(mod, a.out / 'module.ll')
print(json.dumps({k: res.get(k) for k in ('ok', 'unstripped', 'unstripped_sha256')}, indent=1))
