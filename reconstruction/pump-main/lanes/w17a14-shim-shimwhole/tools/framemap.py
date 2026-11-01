#!/usr/bin/env python3
"""framemap.py <execute-slim m.ll> [--llc <debug llc>]: the alloca frame of admin_cto::execute as the backend lays it out.
Runs the assertions llc with -debug-only=stack-coloring,prologepilog (same flags as fastbuild) and prints, per surviving
host frame index in frame order: r10 offset, host size, and the allocas StackColoring merged into it (IR names).
Every alloca below a host whose size or presence changes moves by that delta: a variant's "collapse" is usually such a
uniform frame shift (see tools/fshift.py). Input: a slimmed post-opt module (w17a03/w17a04 rx/<name>/m.ll layout)."""
import sys, os, re, subprocess, collections
a = sys.argv[1:]
llc = os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
if '--llc' in a:
    i = a.index('--llc'); llc = a[i + 1]; del a[i:i + 2]
m = a[0]
r = subprocess.run([llc, '-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections', m,
                    '-filetype=obj', '-o', os.devnull, '-debug-only=stack-coloring,prologepilog'],
                   capture_output=True, text=True)
t = r.stderr
names = {}; sizes = {}
body = re.search(r'^define[^\n]*admin_cto7execute.*?^}', open(m).read(), re.M | re.S).group(0)
for i, n in enumerate(re.findall(r'^\s+%(\S+) = alloca ', body, re.M)):
    names[i] = n
for s, b in re.findall(r'^Slot #(\d+) - (\d+) bytes', t, re.M):
    sizes[int(s)] = int(b)
merged = collections.defaultdict(list)
for h, s in re.findall(r'Merging #(\d+) and slots #(\d+) together', t):
    merged[int(h)].append(int(s))
offs = {int(f): int(o) for f, o in re.findall(r'alloc FI\((\d+)\) at SP\[(-?\d+)\]', t)}
for fi in sorted(offs, key=lambda f: -offs[f]):
    off = offs[fi]
    if fi not in sizes:
        continue  # spill slots / fixed objects
    mem = [names.get(fi, '?')] + [f"{names.get(s, '?')}({sizes.get(s, '?')})" for s in merged.get(fi, [])]
    print(f'{-off:#6x} FI{fi:<4d} {sizes[fi]:4d}B  ' + ' '.join(mem))
