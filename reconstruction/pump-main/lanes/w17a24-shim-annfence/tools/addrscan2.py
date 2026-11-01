#!/usr/bin/env python3
"""addrscan2.py <cand.so>: all add64 rX,imm (not r10-based frame address) in orig vs cand with alignment status, and [rX+0] uses."""
import sys,os,difflib,re,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle, sbpfdis
p=sys.argv[1]
cand=oracle.elf_fn(p,oracle.KEEP) if p.endswith('.so') else open(p,'rb').read()
orig=oracle.orig_window()
O=oracle.mask(orig); C=oracle.mask(cand)
do=sbpfdis.d(orig); dc=sbpfdis.d(cand)
sm=difflib.SequenceMatcher(None,O,C,autojunk=False)
mo={}
for a,b,n in sm.get_matching_blocks():
    for k in range(n): mo[a+k]=b+k
inv={v:k for k,v in mo.items()}
def adds(ds):
    out=[]
    for i in range(len(ds)):
        s=ds[i][1]
        m=re.match(r'add64 (r\d+), (-?\d+)$',s)
        if not m: continue
        x=m.group(1)
        if i>0 and ds[i-1][1]==f'mov64 {x}, r10': continue
        out.append(i)
    return out
for nm,ds,mm,base in (('orig',do,mo,0),('cand',dc,inv,0)):
    A=adds(ds); un=[i for i in A if i not in mm]
    print(nm,'add64 non-frame',len(A),'unmatched',len(un))
    for i in un:
        print('  ',f'{ds[i][0]+0x22a10:x}',' ; '.join(s for _,s in ds[max(0,i-2):i+3]))
