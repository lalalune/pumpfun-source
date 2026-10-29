#!/usr/bin/env python3
"""Build a crate copy while capturing create_token_account_v2 pass dumps (scratch only)."""
import argparse, json, re, subprocess, sys
from pathlib import Path
TOOLS = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction')
sys.path.insert(0, str(TOOLS / 'harness'))
import fastbuild
SYMBOL = "_ZN14pump_recovered10migrate_v223create_token_account_v217hebc7d3eb865ec10dE"
ap = argparse.ArgumentParser()
ap.add_argument('--src', type=Path, required=True); ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--out', type=Path, required=True); ap.add_argument('--sym', default=SYMBOL)
ap.add_argument('--passes', default='before:codegenprepare,after:codegenprepare,after:finalize-isel,before:greedy,after:virtregrewriter,before:block-placement,after:block-placement')
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
mir = a.out / 'mir'; mir.mkdir(exist_ok=True)
llvm = ['-filter-print-funcs=' + a.sym]
for p in a.passes.split(','):
    w, n = p.split(':'); llvm.append(f'-print-{w}={n}')
extra = ['--emit=link,llvm-ir', '-Zdump-mir=create_token_account_v2', '-Zdump-mir-dir=' + str(mir.resolve()), '-Zdump-mir-exclude-pass-number'] + [x for v in llvm for x in ('-C', 'llvm-args=' + v)]
real = subprocess.run
def run(cmd, *ra, **kw):
    if isinstance(cmd, list) and len(cmd) > 1 and str(cmd[0]).endswith('/cargo') and cmd[1] == 'build':
        cmd = cmd[:]; cmd[1] = 'rustc'; cmd += ['--lib', '--'] + extra
    return real(cmd, *ra, **kw)
subprocess.run = run
try:
    res = fastbuild.build(a.src, a.work, a.out, recipe='identity')
finally:
    subprocess.run = real
text = (a.out / 'build.log').read_text(errors='replace')
chunks = re.split(r'(?=# \*\*\* IR Dump |\*\*\* IR Dump )', text)
n = 0
for c in chunks:
    if 'IR Dump' not in c.splitlines()[0] if c else True: continue
    h = c.splitlines()[0]; st = re.sub(r'[^a-z0-9]+', '-', h.lower()).strip('-')[:80]
    (a.out / f'dump-{n:02d}-{st}.txt').write_text(c); n += 1
mod = a.work / 'target-identity/sbpf-solana-solana/release/deps/pump_recovered.ll'
if mod.exists():
    t = mod.read_text()
    m = re.search(r'^define[^\n]*' + re.escape(a.sym) + r'[^\n]*\n.*?^\}', t, re.M | re.S)
    if m: (a.out / 'final.ll').write_text(m.group(0) + '\n')
res['dumps'] = n
print(json.dumps(res, indent=1))
