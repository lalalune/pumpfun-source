#!/usr/bin/env python3
"""Scratch-only: build crate copy with --emit=link,llvm-ir (no source change); copy module .ll to OUT."""
import argparse, json, subprocess, sys, shutil
from pathlib import Path
TOOLS = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction')
sys.path.insert(0, str(TOOLS / 'harness'))
import fastbuild
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True)
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
extra = ['--emit=link,llvm-ir', '-Zfewer-names=no']
real = subprocess.run
def run(cmd, *ra, **kw):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
subprocess.run = run
try:
    res = fastbuild.build(a.src, a.work, a.out, recipe='identity')
finally:
    subprocess.run = real
mod = a.work / 'target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll'
if mod.exists(): shutil.copy(mod, a.out / 'module.ll')
print(json.dumps(res, indent=1))
