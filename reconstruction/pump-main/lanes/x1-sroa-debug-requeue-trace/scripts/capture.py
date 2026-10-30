#!/usr/bin/env python3
"""capture.py SRC_PUMP_DIR OUTDIR: diagnostic build that dumps the module before every SROA run on
create_v2::execute (-print-before=sroa -print-module-scope) and splits the dumps into OUTDIR/m<i>.ll."""
import sys, os, re
from pathlib import Path
L = 'x1-sroa-debug-requeue-trace'
C = Path.home() / f'.cache/pumpfun-reconstruction/lanes/{L}'
H = Path(__file__).resolve().parents[4] / 'harness'
sys.path.insert(0, str(H))
import fastbuild
src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
FN = '_ZN14pump_recovered9create_v27execute17h3f7d08900031c023E'
args = ['-print-before=sroa', '-print-module-scope', f'-filter-print-funcs={FN}']
real = fastbuild.run_compiler
def hook(cmd, *a, **k):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + [x for v in args for x in ('-C', 'llvm-args=' + v)]
    return real(cmd, *a, **k)
fastbuild.run_compiler = hook
r = fastbuild.build(src, C / 'work-cap', out, quiet=True)
log = (out / 'build.log').read_text(errors='replace')
parts = re.split(r'(?m)^; \*\*\* IR Dump Before SROAPass[^\n]*\n', log)
n = 0
for p in parts[1:]:
    j = p.find('\n   Compiling'); p = p if j < 0 else p[:j]
    (out / f'm{n}.ll').write_text(p); n += 1
(out / 'build.log').write_text('dumps split: %d\n' % n)
print({'ok': r.get('ok'), 'dumps': n})
