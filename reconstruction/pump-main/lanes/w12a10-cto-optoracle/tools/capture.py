#!/usr/bin/env python3
"""Lane-local experiment capture (never for proposals): identity build of a crate copy with
--emit=link,llvm-ir and -C save-temps (keeps the pre-optimization *.no-opt.bc module).
capture.py <src crate> <work> <out> [extra rustc args...]"""
import sys, json, shutil
from pathlib import Path
T = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a10-cto-optoracle/reconstruction/harness')
sys.path.insert(0, str(T)); import fastbuild
src, work, out = map(Path, sys.argv[1:4]); extra = sys.argv[4:]
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,llvm-ir', '-C', 'save-temps'] + extra
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
out.mkdir(parents=True, exist_ok=True)
for p in work.glob('target*/*/release/deps/pump_recovered*.ll'):
    shutil.copy2(p, out / 'pump_recovered.ll')
for p in work.glob('target*/*/release/deps/pump_recovered*no-opt*.bc'):
    shutil.copy2(p, out / p.name)
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped', 'unstripped_sha256')}, indent=1))
