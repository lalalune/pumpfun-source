#!/usr/bin/env python3
"""pexit.py in.ll out.ll preds(comma) [9]: IR oracle: move the join bb74's 7-byte (and with '9' also the 9-byte) target copy
into a fresh block on each listed predecessor edge (per-exit join copies, as the original 0x23b50/0x24268 blocks). Oracle only."""
import sys,re
src,dst,preds=sys.argv[1:4]; nine=len(sys.argv)>4
t=open(src).read()
k=t.index('\nbb74:'); e=t.index('\n\n',k+1); x=t[k:e]; L=x.split('\n')
c7=[l for l in L if 'memcpy' in l and 'dereferenceable(7) %target.sroa.0, ptr noundef nonnull align 1 dereferenceable(7) %target.i.sroa.0' in l]
c9=[l for l in L if 'memcpy' in l and '%_48.sroa.11, ptr noundef nonnull align 1 dereferenceable(9) %target.i.sroa.9' in l]
mv=c7+(c9 if nine else [])
L=[l for l in L if l not in mv]
allp=['bb58.i','bb44.i','bb45.i']
P=preds.split(',')
newblocks=[]
for p in P:
    nb='pe.'+p.replace('.','_')
    # retarget pred's branch to bb74 -> nb
    pk=t.index('\n'+p+':'); pe=t.index('\n\n',pk+1); px=t[pk:pe]
    px2=re.sub(r'label %bb74\b','label %'+nb,px,count=1); assert px2!=px
    t=t[:pk]+px2+t[pe:]
    newblocks.append('\n'+nb+':\n'+'\n'.join(mv)+'\n  br label %bb74\n')
    L=[re.sub(r'(\[ [^\]]+, )%'+re.escape(p)+r' \]',r'\1%'+nb+' ]',l) if l.lstrip().startswith('%') and ' phi ' in l else l for l in L]
L[0]=L[0].split(';')[0].rstrip()
x='\n'.join(L)
k=t.index('\nbb74:'); e=t.index('\n\n',k+1)
t=t[:k]+x+t[e:]
e=t.index('\n\n',t.index('\nbb74:')+1)
t=t[:e]+'\n'+''.join(newblocks)+t[e:]
open(dst,'w').write(t)
