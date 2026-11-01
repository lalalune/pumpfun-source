#!/usr/bin/env python3
"""capopt.py <crate> <work> <out>: identity build that also emits rustc's POST-opt LLVM IR (what codegen consumes) and writes
<out>/m.ll, the module slimmed to admin_cto::execute (other functions become declarations), ready for framemap.py / llc.
Experiment only (adds --emit=llvm-ir to the final rustc invocation)."""
import sys, json, shutil, re
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
for p in work.glob('target*/*/release/deps/pump_recovered*.ll'):
    p.unlink()
r = fastbuild.build(src, work, out, recipe='identity')
lls = list(work.glob('target*/*/release/deps/pump_recovered*.ll'))
if not lls:
    print(json.dumps({'ok': False})); sys.exit(1)
t = lls[0].read_text()
def slim(t, keep=r'admin_cto7execute'):
    res = []; skip = False
    for l in t.split('\n'):
        if skip:
            if l == '}': skip = False
            continue
        if l.startswith('define '):
            m = re.match(r'define (.*?)@("[^"]+"|[\w.$]+)\(', l)
            if not re.search(keep, m.group(2)):
                d = l[len('define '):].rstrip(); d = d[:-1].rstrip()
                for _ in range(2):
                    d = re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|unnamed_addr)\s+', '', d)
                d = re.sub(r'\s+comdat(\([^)]*\))?', '', d); d = re.sub(r'\s+personality\s+ptr\s+@\S+', '', d)
                d = re.sub(r' (%[\w.$"]+)(?=[,)])', '', d)
                res.append('declare ' + d); skip = True; continue
        if re.match(r'^@\S+ = .*\balias\b', l): continue
        res.append(l)
    return '\n'.join(res)
(out / 'm.ll').write_text(slim(t))
for p in lls: p.unlink()
print(json.dumps({'ok': r.get('ok'), 'm': str(out / 'm.ll')}))
