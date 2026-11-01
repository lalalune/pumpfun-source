#!/usr/bin/env python3
"""caplines.py <crate> <work> <out>: identity build that also emits asm with line tables (experiment only, for source mapping)."""
import sys, json, shutil
from pathlib import Path
H = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a03-cto-revidiom/reconstruction/harness')
sys.path.insert(0, str(H)); import fastbuild
src, work, out = map(Path, sys.argv[1:4])
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,asm', '-C', 'debuginfo=line-tables-only']
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
for p in work.glob('target*/*/release/deps/pump_recovered*.s'):
    shutil.copy2(p, out / 'lines.s')
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped')}, indent=1))
