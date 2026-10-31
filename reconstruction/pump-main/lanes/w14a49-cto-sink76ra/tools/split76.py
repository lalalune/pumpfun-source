#!/usr/bin/env python3
"""split76.py in.ll out.ll MODE [PREDS] : split the edges into bb76 (post-opt IR oracle, experiment only).
MODE asm   : each split block holds an empty sideeffect asm (keeps it from being folded)
MODE copy  : each split block holds bb76's target-piece memcpys + lifetime.ends (bb76 keeps only phis + shared br)
MODE copyA : like copy but only the 7-byte piece goes to the split blocks; the 9-byte piece stays in bb76
PREDS: comma list of bb76 preds to split (default all: bb45.i,bb58.i,bb44.i)."""
import sys,re
src,dst,mode=sys.argv[1:4]
preds=(sys.argv[4] if len(sys.argv)>4 else 'bb45.i,bb58.i,bb44.i').split(',')
t=open(src).read()
i=t.index('\nbb76:'); j=t.index('br i1 %shared.sroa.0.0.off0, label %bb19, label %bb22',i)
blk=t[i:j].split('\n')
cp=[l for l in blk if 'memcpy' in l or 'lifetime.end' in l]
if mode=='copyA': cp=[l for l in cp if 'target.sroa.0, ptr' in l or 'i64 7, ptr nonnull %target.i.sroa.0' in l]
body={'asm':['  call void asm sideeffect "", ""()'],'copy':cp,'copyA':cp}[mode]
if mode in('copy','copyA'):
    blk=[l for l in blk if l not in cp]; t=t[:i]+'\n'.join(blk)+t[j:]
    # phis in bb76 reference the copied allocas? no: copies are on allocas, phis are SSA. ok.
new=''
for p in preds:
    k=t.index('\n'+p+':'); e=t.index('\n\n',k+1); b=t[k:e]
    term=b.rstrip().split('\n')[-1]
    assert '%bb76' in term,(p,term)
    nb=f'bb76.s{p.replace(".","_")}'
    b2=b[:b.rindex(term)]+term.replace('label %bb76',f'label %{nb}')
    t=t[:k]+b2+t[e:]
    new+=f'\n{nb}:                                             ; preds = %{p}\n'+'\n'.join(body)+'\n  br label %bb76\n'
    # fix phis of bb76
    i=t.index('\nbb76:'); j=t.index('\n\n',i+1); hb=t[i:j]
    hb=re.sub(r', %'+re.escape(p)+r' \]',f', %{nb} ]',hb); hb=hb.replace('%'+p+',','%'+nb+',').replace('%'+p+'\n','%'+nb+'\n')
    hb=re.sub(r'(; preds = .*)%'+re.escape(p)+r'\b',r'\1%'+nb,hb,count=1)
    t=t[:i]+hb+t[j:]
i=t.index('\nbb76:'); t=t[:i]+new+t[i:]
open(dst,'w').write(t)
