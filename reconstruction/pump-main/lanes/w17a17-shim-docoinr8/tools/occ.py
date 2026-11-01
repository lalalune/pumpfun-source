#!/usr/bin/env python3
"""occ.py <ra.txt> <vreg> [nth] : replay a -debug-only=regalloc trace; at the nth (default 1) 'selectOrSplit GPR:%vreg'
print, per CSR r6..r9 (and r0..r5 with --all), the assigned vregs whose live interval overlaps the target's, with weights."""
import sys, re
p = sys.argv[1]; tv = sys.argv[2].lstrip('%'); nth = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1
allr = '--all' in sys.argv
def segs(s):
    out = []
    for a, b in re.findall(r'\[(\d+)[rBed],(\d+)[rBed]:\d+\)', s):
        out.append((int(a), int(b)))
    return out
asg = {}; ivl = {}; wt = {}; cnt = 0
for l in open(p):
    if l.startswith('selectOrSplit GPR:%'):
        m = re.match(r'selectOrSplit GPR:%(\d+) (.*?)  weight:(\S+)', l)
        if not m: continue
        v = m.group(1); ivl[v] = segs(m.group(2)); wt[v] = m.group(3)
        if v == tv:
            cnt += 1
            if cnt == nth: break
        continue
    m = re.match(r'assigning %(\d+) to \$(r\d+): \S+ (.*)', l)
    if m:
        v = m.group(1); asg[v] = m.group(2)
        s = segs(m.group(3))
        if s: ivl[v] = s
        continue
    m = re.match(r'unassigning %(\d+) from \$(r\d+)', l)
    if m:
        asg.pop(m.group(1), None); continue
T = ivl[tv]
def ov(a, b):
    i = j = 0; n = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0]); hi = min(a[i][1], b[j][1])
        if lo < hi: n += hi - lo
        if a[i][1] < b[j][1]: i += 1
        else: j += 1
    return n
regs = ['r0','r1','r2','r3','r4','r5','r6','r7','r8','r9'] if allr else ['r6','r7','r8','r9']
print(f'target %{tv} dequeue#{nth} w={wt.get(tv)} span={T[0][0]}..{T[-1][1]} size={sum(b-a for a,b in T)}')
for r in regs:
    hs = [(v, ov(T, ivl[v])) for v, rr in asg.items() if rr == r and v in ivl]
    hs = [(v, o) for v, o in hs if o > 0]
    hs.sort(key=lambda x: -x[1])
    print(r, ' '.join(f'%{v}(ov{o},w{float(wt.get(v,"0")):.2e},{ivl[v][0][0]}..{ivl[v][-1][1]})' for v, o in hs))
