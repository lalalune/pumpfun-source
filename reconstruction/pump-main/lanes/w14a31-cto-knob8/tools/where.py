#!/usr/bin/env python3
"""where.py base name...: first and last cand offset where name's tokens differ from base (difflib), i.e. where a knob acts."""
import sys,os,difflib
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a31-cto-knob8')
def jmk(t):
    out=[]
    for x in t:
        op=x[0]
        if (op&7) in (5,6) and op not in (0x85,0x95): x=x[:2]+b'\0\0'+x[4:]
        out.append(x)
    return out
def ld(n): return jmk(mask(open(f'{O}/rx/{n}/fn.bin','rb').read()))
b=ld(sa[1])
for n in sa[2:]:
    c=ld(n); sm=difflib.SequenceMatcher(None,b,c,autojunk=False)
    ops=[o for o in sm.get_opcodes() if o[0]!='equal']
    if not ops: print(n,'identical'); continue
    sz=[(o[1]*8,o[2]-o[1],o[4]-o[3]) for o in ops]
    print('%-18s base tok %5d..%5d (~0x%05x..0x%05x)  n_ops %d'%(n,ops[0][1],ops[-1][2],ops[0][1]*8,ops[-1][2]*8,len(ops)),[('%05x'%a,x,y) for a,x,y in sz][:8])
