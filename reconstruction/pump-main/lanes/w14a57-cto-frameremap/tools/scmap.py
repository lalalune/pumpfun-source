#!/usr/bin/env python3
"""scmap.py <m.ll> [outdir] : StackColoring class map of admin_cto::execute (experiment only).
Runs llvm-dbg llc -debug-only=stack-coloring and llc -stop-after=prologepilog on the slimmed module m.ll (rx.py output),
prints every final frame object (offset, size) with the allocas StackColoring merged into it, plus each alloca's
lifetime-marker count. Use it to see which allocas share a colour class and where the representative lands."""
import sys, os, re, subprocess, collections, json
ml = sys.argv[1]; d = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(ml))
SDK = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
DL = os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc')
F = ['-O3', '-relocation-model=pic', '-mattr=+store-imm,+jmp-ext', '-function-sections']
r = subprocess.run([DL] + F + [ml, '-filetype=obj', '-o', d + '/_dbg.o', '-debug-only=stack-coloring'], capture_output=True, text=True)
log = r.stderr; os.remove(d + '/_dbg.o')
subprocess.run([SDK + '/llc'] + F + [ml, '-stop-after=prologepilog', '-o', d + '/post.mir'], check=True)
# only execute's section
log = log.split('admin_cto7execute', 1)[1].split('********** Stack Coloring', 1)[0]
name = {}; size = {}
for m in re.finditer(r'slot #(\d+) with allocation: (\S+)', log): name[int(m.group(1))] = m.group(2)
for m in re.finditer(r'^Slot #(\d+) - (\d+) bytes', log, re.M): size[int(m.group(1))] = int(m.group(2))
mem = collections.defaultdict(list)
for m in re.finditer(r'Merging #(\d+) and slots #(\d+)', log): mem[int(m.group(1))].append(int(m.group(2)))
post = open(d + '/post.mir').read()
post = post[post.index('admin_cto7execute'):]
off = {}
for m in re.finditer(r'id: (\d+), name: ([^,]*), type: default, offset: (-?\d+), size: (\d+)', post.split('\nstack:', 1)[1].split('\ncallSites', 1)[0]):
    off[int(m.group(1))] = (int(m.group(3)), int(m.group(4)), m.group(2))
rows = []
for i, (o, s, nm) in sorted(off.items(), key=lambda kv: -kv[1][0]):
    ms = [(j, name.get(j, '?'), size.get(j)) for j in mem.get(i, [])]
    rows.append({'id': i, 'name': nm, 'off': o, 'size': s, 'members': ms})
    print(f'{-o:#06x} {s:4d} #{i:<3d} {nm:28s} <- ' + ' '.join(f'#{j}:{n}({z})' for j, n, z in ms))
json.dump(rows, open(d + '/scmap.json', 'w'), indent=0)
