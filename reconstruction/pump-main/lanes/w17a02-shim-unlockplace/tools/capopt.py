#!/usr/bin/env python3
"""capopt.py <crate> <work> <out>: identity build that also emits rustc's post-optimization LLVM IR (pre-codegen). Experiment only."""
import sys, json, shutil
from pathlib import Path
H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
sys.path.insert(0, str(H)); import fastbuild
src, work, out = map(Path, sys.argv[1:4]); out.mkdir(parents=True, exist_ok=True)
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,llvm-ir']
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
for p in work.glob('target*/*/release/deps/pump_recovered*.ll'):
    shutil.copy2(p, out / 'opt.ll'); p.unlink()
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped')}, indent=1))
