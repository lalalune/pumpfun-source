#!/usr/bin/env python3
"""Lane-local experiment only (never for proposals): build a crate copy with --emit=link,llvm-ir.
capture_ir.py <src crate> <work> <out> [--raw] [llvm-arg ...]
Post-opt IR lands in <out>/pump_recovered.ll (with --raw: pre-opt IR, -C no-prepopulate-passes)."""
import sys, json, shutil
from pathlib import Path
HERE = Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / 'reconstruction' / 'harness').is_dir())
sys.path.insert(0, str(ROOT / 'reconstruction' / 'harness'))
import fastbuild, build_process  # noqa: E402
src, work, out = map(Path, sys.argv[1:4]); rest = sys.argv[4:]
raw = '--raw' in rest; llvm = [x for x in rest if x != '--raw']
real = build_process.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'
        cmd += ['--lib', '--', '--emit=link,llvm-ir'] + (['-C', 'no-prepopulate-passes'] if raw else []) \
            + [x for v in llvm for x in ('-C', 'llvm-args=' + v)]
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, work, out, recipe='identity')
for p in Path(work).glob('target*/*/release/deps/pump_recovered*.ll'):
    shutil.copy2(p, Path(out) / 'pump_recovered.ll')
print(json.dumps({k: r.get(k) for k in ('ok', 'unstripped')}))
