#!/usr/bin/env python3
"""csrlive.py <dis> <lo> <hi>: for each call in [lo,hi), callee-saved regs (r6-r9) read after it before being written."""
import re,sys
L=[(int(l.split(None,1)[0],16),l.split(None,1)[1].strip()) for l in open(sys.argv[1])]
lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
out=[]
for idx,(c,ins0) in enumerate(L):
    if not(lo<=c<hi and ins0.startswith('call')): continue
    live=set(); w=set()
    for x,ins in L[idx+1:idx+150]:
        if ins.startswith('call') or ins.startswith('exit'): break
        regs=re.findall(r'\br(\d+)\b',ins); op=ins.split()[0]
        if op.startswith('st') or op.startswith('j'): reads,writes=regs,[]
        elif op in('mov64','mov32','lddw') or op.startswith('ldx'): writes,reads=regs[:1],regs[1:]
        else: writes,reads=regs[:1],regs
        for r in reads:
            if r in ('6','7','8','9') and r not in w: live.add('r'+r)
        w.update(writes)
    out.append('%x:%s'%(c,''.join(sorted(live)) or '-'))
print(' '.join(out))
