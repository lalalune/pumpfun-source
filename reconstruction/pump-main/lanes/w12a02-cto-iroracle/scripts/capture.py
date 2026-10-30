#!/usr/bin/env python3
"""capture.py <crate> <work> <out> [rustc flags...]: identity build of a scratch crate copy that also
emits the post-opt LLVM IR (out/pump_recovered.ll). Experiment-only: never use for proposals.
Uses this worktree's harness fastbuild (slot-locked like measure.sh)."""
import sys, json, shutil
from pathlib import Path
H = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(H)); import fastbuild
src, work, out = map(Path, sys.argv[1:4]); extra = sys.argv[4:]
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--', '--emit=link,llvm-ir'] + extra
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
try:
    r = fastbuild.build(src, work, out, recipe='identity')
finally:
    fastbuild.run_compiler = real
if r.get('ok'):
    d = work / 'target-identity/sbpf-solana-solana/release/deps'
    for p in sorted(d.glob('pump_recovered*.ll'), key=lambda p: p.stat().st_mtime)[-1:]:
        shutil.copy2(p, out / 'pump_recovered.ll')
print(json.dumps(r, indent=1))
