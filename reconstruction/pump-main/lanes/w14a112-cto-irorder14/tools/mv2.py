#!/usr/bin/env python3
"""mv2.py base.ll out.ll move... : post-opt IR block moves in execute. move = U1+U2..@X (units placed before X) or U..>X (after X).
Short names (to_string exits as exitNN.i); first occurrence wins. Experiment only."""
import sys,re
def load(text):
    L=text.split('\n')
    fs=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
    fe=fs+[k for k,l in enumerate(L[fs:]) if l=='}'][0]
    st=[i for i in range(fs+1,fe) if re.match(r'^("[^"]+"|[\w.$-]+):',L[i])]
    bl=[]
    for k,i in enumerate(st):
        e=st[k+1] if k+1<len(st) else fe
        n=re.match(r'^("[^"]+"|[\w.$-]+):',L[i]).group(1).strip('"')
        bl.append([n,L[i:e]])
    return L[:st[0]],bl,L[fe:]
def short(n): return n.split('E.')[-1] if 'to_string' in n else n
def idx(bl,nm):
    for i,b in enumerate(bl):
        if short(b[0])==nm or b[0]==nm: return i
    raise SystemExit('no block '+nm)
def move(bl,spec):
    after='>' in spec
    u,x=spec.split('>' if after else '@')
    ids=[idx(bl,n) for n in u.split('+')]
    blocks=[bl[i] for i in ids]; rest=[b for i,b in enumerate(bl) if i not in ids]
    k=idx(rest,x)+(1 if after else 0)
    return rest[:k]+blocks+rest[k:]
H,BL,T=load(open(sys.argv[1]).read())
for s in sys.argv[3:]: BL=move(BL,s)
open(sys.argv[2],'w').write('\n'.join(H+[l for b in BL for l in b[1]]+T))
