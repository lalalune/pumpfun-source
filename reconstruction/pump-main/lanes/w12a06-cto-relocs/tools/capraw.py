#!/usr/bin/env python3
"""Lane-local experiment only: build a crate copy with --emit=link,llvm-ir and -C no-prepopulate-passes (raw IR).
capraw.py <src crate> <work> <out> [raw|opt]"""
import sys, json, shutil
from pathlib import Path
T = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(T)); import fastbuild
src, work, out = map(Path, sys.argv[1:4]); mode = sys.argv[4] if len(sys.argv) > 4 else 'raw'
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,llvm-ir'] + (['-C', 'no-prepopulate-passes'] if mode == 'raw' else [])
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
for p in work.glob('target*/*/release/deps/pump_recovered*.ll'):
    shutil.copy2(p, out / f'pump_recovered.{mode}.ll')
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped', 'seconds')}, indent=1))
