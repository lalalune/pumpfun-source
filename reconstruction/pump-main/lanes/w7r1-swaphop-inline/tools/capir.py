#!/usr/bin/env python3
"""Scratch-only: build crate copy with --emit=link,llvm-ir; copy module .ll to OUT."""
import argparse, json, sys, shutil
from pathlib import Path
sys.path.insert(0, '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-swaphop-inline/reconstruction/harness')
import fastbuild
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--extra', default='')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
extra = ['--emit=link,llvm-ir,mir', '-Zfewer-names=no'] + a.extra.split()
real = fastbuild.run_compiler
def run(cmd, *ra, **kw):
    cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
fastbuild.run_compiler = run
res = fastbuild.build(a.src, a.work, a.out)
for m in a.work.rglob('pump_recovered*.ll'):
    shutil.copy(m, a.out / 'module.ll'); break
for m in a.work.rglob('pump_recovered*.mir'):
    shutil.copy(m, a.out / 'module.mir'); break
print(json.dumps({k:res.get(k) for k in ('ok','unstripped_sha256')}))
