#!/usr/bin/env python3
"""spillprobe.py <in m.ll> <out m.ll> <%value> [--vol] [--only N,M]: IR probe 'spill at def' (experiment only).
Stores %value to a fresh entry alloca right after its definition (after the phis if it is a phi) and replaces every use
outside the defining block (non-phi uses) by a load of that alloca placed right before the using instruction.
Source analogue: the value is not held as an SSA local across the region (it lives in memory, as when the original's RA
spilled it at its definition). --only restricts to the listed use indices (1-based, in file order)."""
import sys, re
a = sys.argv[1:]; src, dst, v = a[0], a[1], a[2]; vol = '--vol' in a
import hashlib; TAG = 'sp' + hashlib.md5(v.encode()).hexdigest()[:6]
only = None
if '--only' in a: only = set(int(x) for x in a[a.index('--only') + 1].split(','))
L = open(src).read().split('\n')
st = [i for i, l in enumerate(L) if l.startswith('define ')][0]
en = st + next(i for i, l in enumerate(L[st:]) if l == '}')
vre = re.escape(v) + r'(?![\w.$])'
di = next(i for i in range(st, en) if re.match(r'\s+' + vre + r' = ', L[i]))
dl = L[di]; m = re.match(r'\s+%\S+ = (?:getelementptr inbounds i8, )?(\w+|ptr)', dl)
ty = 'ptr' if (' getelementptr ' in dl or ' = load ptr' in dl or 'inttoptr' in dl) else None
if ty is None:
    mm = re.match(r'\s+%\S+ = (?:load|phi|zext|sext|trunc|add|sub|and|or|xor|select i1 %\S+,|icmp \w+|lshr|shl|mul) (\w+)', dl)
    ty = mm.group(1) if mm else 'i64'
    if ' = icmp ' in dl: ty = 'i1'
    if ' = select ' in dl: ty = re.search(r'select i1 %\S+, (\w+)', dl).group(1)
def blk(i):
    for j in range(i, st, -1):
        if re.match(r'^("[^"]+"|[\w.$-]+):', L[j]): return j
    return st
db = blk(di)
ins_at = di + 1
if ' = phi ' in dl:
    while ' = phi ' in L[ins_at]: ins_at += 1
q = ' volatile' if vol else ''
uses = [i for i in range(st + 1, en) if i != di and re.search(vre, L[i]) and ' = phi ' not in L[i] and blk(i) != db]
sel = [u for k, u in enumerate(uses, 1) if only is None or k in only]
out = []; n = 0
for i, l in enumerate(L):
    if i == st + 1: out.append(l); out.append('  %%%s_slot = alloca %s, align 8' % (TAG, 'i8' if ty == 'i1' else ty)); continue
    if i in sel:
        n += 1; nm = '%%%s_ld%d' % (TAG, n)
        out.append('  %s = load%s %s, ptr %%%s_slot, align 8' % (nm, q, 'i8' if ty == 'i1' else ty, TAG))
        if ty == 'i1':
            out.append('  %s.b = trunc i8 %s to i1' % (nm, nm)); nm = nm + '.b'
        out.append(re.sub(vre, nm, l)); continue
    out.append(l)
    if i == ins_at - 1:
        if ty == 'i1':
            out.append('  %%%s_z = zext i1 %s to i8' % (TAG, v)); out.append('  store%s i8 %%%s_z, ptr %%%s_slot, align 8' % (q, TAG, TAG))
        else:
            out.append('  store%s %s %s, ptr %%%s_slot, align 8' % (q, ty, v, TAG))
open(dst, 'w').write('\n'.join(out))
print('value %s type %s def line %d, uses outside def block %d, replaced %d' % (v, ty, di + 1, len(uses), len(sel)), file=sys.stderr)
