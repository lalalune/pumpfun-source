#!/usr/bin/env python3
"""dd.py NAME [--ctx N] [--full]: diff an orc.py oracle object (orc/NAME/m.o) against the original swap_hop.
Calls are shown by callee name (orig call targets mapped through call order), jump offsets masked.
Prints hunks with original offsets (fn-relative) and a summary."""
import sys, os, re, subprocess, difflib, argparse, json
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w10r1-swaphop-ir')
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--ctx', type=int, default=2)
ap.add_argument('--frm', type=lambda x: int(x, 0), default=0); ap.add_argument('--to', type=lambda x: int(x, 0), default=1 << 30)
ap.add_argument('--stat', action='store_true')
a = ap.parse_args()
def dm(n): return re.sub(r'17h[0-9a-f]{16}E$', '', n).split('..')[-1][-40:]
def cand(name):
    txt = subprocess.run([L + '/llvm-objdump', '-d', '--no-show-raw-insn', '-r', f'{O}/orc/{name}/m.o'], capture_output=True, text=True).stdout
    sec = txt.split('multi_hop_curve8swap_hop17h', 1)[1]
    out = []; pend = None
    for l in sec.splitlines()[2:]:
        if l.startswith('Disassembly of section'): break
        m = re.search(r'R_SBF_64_32\s+(\S+)', l)
        if m:
            if out and out[-1][1].startswith('call'): out[-1][1] = 'call ' + dm(m.group(1))
            continue
        if 'R_SBF' in l: continue
        m = re.match(r'\s+(\d+):\s+(.*)', l)
        if m:
            s = re.sub(r'\s*<[^>]*>$', '', m.group(2).strip()); out.append([int(m.group(1)) * 8, s]); continue
    # lddw occupies 2 slots: objdump numbers by slot already
    return out
def orig():
    out = []
    for l in open(O + '/orig.txt'):
        m = re.match(r'(0x[0-9a-f]+)\s+(.*)', l)
        if m: out.append([int(m.group(1), 16) - 0x5b3b0, m.group(2).strip()])
    return out
o = orig(); c = cand(a.name)
oc = [i for i, x in enumerate(o) if x[1].startswith('call ') and not x[1].startswith('call 0x') is None]
# map orig call targets -> names via order alignment with reference oracle 'x1' (call order exact)
ref = cand('x1') if a.name != 'x1' else c
rc = [x[1] for x in ref if x[1].startswith('call ')]
ocs = [(i, x) for i, x in enumerate(o) if x[1].startswith('call ')]
mp = {}
for (i, x), n in zip(ocs, rc):
    mm = re.match(r'call (-?0x[0-9a-f]+)', x[1])
    if mm: mp[x[0] + 8 + int(mm.group(1), 16) * 8] = n
for x in o:
    mm = re.match(r'call (-?0x[0-9a-f]+)', x[1])
    if mm: x[1] = mp.get(x[0] + 8 + int(mm.group(1), 16) * 8, x[1])
def norm(s):
    if s.startswith('lddw'): return re.sub(r', .*$', ', IMM', s)
    return re.sub(r'([+-]0x[0-9a-f]+)$', '', s) if s.startswith('j') else s
on = [norm(x[1]) for x in o]; cn = [norm(x[1]) for x in c]
sm = difflib.SequenceMatcher(None, on, cn, autojunk=False)
print(json.dumps({'ratio_masked': round(sm.ratio(), 5), 'orig': len(o), 'cand': len(c), 'equal': sum(b.size for b in sm.get_matching_blocks())}))
if a.stat: sys.exit()
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal': continue
    if not (a.frm <= o[min(i1, len(o) - 1)][0] < a.to): continue
    print(f'@@ {op} orig {o[i1][0] if i1 < len(o) else -1:#x} ({i2 - i1}) cand {c[j1][0] if j1 < len(c) else -1:#x} ({j2 - j1})')
    for k in range(max(0, i1 - a.ctx), i1): print(f'   {o[k][0]:#7x}        {o[k][1]}')
    for k in range(i1, i2): print(f' - {o[k][0]:#7x}        {o[k][1]}')
    for k in range(j1, j2): print(f' +        {c[k][0]:#7x} {c[k][1]}')
