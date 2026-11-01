#!/usr/bin/env python3
"""Lane-local IR/MIR capture (never used for proposals). Builds a crate copy through the w11-baseline
fastbuild (identity recipe) as `cargo rustc --lib -- --emit=link,llvm-ir <rustc args>` and keeps the .ll,
the compiler log and any MIR dumps. Extends w16a01's capture_ir.py with raw rustc args.
Usage: capture2.py <src> <work> <out> [--rustc ARG]... [--llvm ARG]...
  e.g. --rustc -Zdump-mir=buy_body --rustc -Zdump-mir-dir=/abs/out/mir --llvm -print-after=sroa"""
import sys, shutil, json
from pathlib import Path
H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0, str(H))
import fastbuild
src, work, out = map(Path, sys.argv[1:4])
rustc, llvm = [], []
a = sys.argv[4:]
for i in range(0, len(a), 2):
    (rustc if a[i] == '--rustc' else llvm).append(a[i + 1])
real = fastbuild.run_compiler
def hook(cmd, *x, **k):
    cmd = list(cmd)
    if len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd[1] = 'rustc'
        cmd += ['--lib', '--', '--emit=link,llvm-ir'] + rustc + [y for v in llvm for y in ('-C', 'llvm-args=' + v)]
    return real(cmd, *x, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
if r.get('ok'):
    for p in (work / 'target-identity').glob('*/release/deps/pump_recovered*.ll'):
        shutil.copy2(p, out / 'pump_recovered.ll')
print(json.dumps(r, indent=1)[:2000])
