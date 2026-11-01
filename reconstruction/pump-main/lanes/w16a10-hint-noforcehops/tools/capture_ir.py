#!/usr/bin/env python3
"""Lane-local IR capture (never used for proposals): build a crate copy with cargo rustc --emit=link,llvm-ir
plus optional -C llvm-args, and keep the .ll and the compiler log. Usage: capture_ir.py <src> <work> <out> [llvm-arg ...]"""
import sys, shutil, json
from pathlib import Path
H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0, str(H))
import fastbuild
src, work, out = map(Path, sys.argv[1:4]); llvm = sys.argv[4:]
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    cmd = list(cmd)
    if len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd[1] = 'rustc'
        cmd += ['--lib', '--', '--emit=link,llvm-ir'] + [x for v in llvm for x in ('-C', 'llvm-args=' + v)]
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
if r.get('ok'):
    for p in (work / 'target-identity').glob('*/release/deps/pump_recovered*.ll'):
        shutil.copy2(p, out / 'pump_recovered.ll')
print(json.dumps(r, indent=1)[:2000])
