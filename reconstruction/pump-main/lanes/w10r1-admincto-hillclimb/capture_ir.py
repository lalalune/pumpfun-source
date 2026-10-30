#!/usr/bin/env python3
"""Lane-local experiment: build a scratch crate copy with --emit llvm-ir too (never for proposals).
capture_ir.py <src crate> <work> <out> [llvm-arg ...]"""
import sys, subprocess, json, shutil
from pathlib import Path
T = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w10r1-admincto-hillclimb/reconstruction/harness')
sys.path.insert(0, str(T)); import fastbuild, build_process
src, work, out = map(Path, sys.argv[1:4]); llvm = sys.argv[4:]
real = build_process.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,llvm-ir'] + [x for v in llvm for x in ('-C', 'llvm-args=' + v)]
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
for p in work.glob('target*/*/release/deps/pump_recovered*.ll'):
    shutil.copy2(p, out / 'pump_recovered.ll')
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped')}, indent=1))
