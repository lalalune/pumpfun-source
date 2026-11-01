#!/usr/bin/env python3
"""addrscan.py <cand.so|fn.bin>: list orig 'mov64 rX,rY; add64 rX,imm' (rY!=r10) address formations and how they align to cand."""
import sys,os,difflib
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
def pairs(ds):
    out=[]
    for i in range(len(ds)-1):
        s1=ds[i][1]; s2=ds[i+1][1]
        if s1.startswith('mov64 r') and s2.startswith('add64 r'):
            x=s1.split()[1].rstrip(','); y=s1.split()[2]
            if y.startswith('r') and y!='r10' and s2.split()[1].rstrip(',')==x: out.append(i)
    return out
po=pairs(do); pc=pairs(dc)
print('orig pairs',len(po),'cand pairs',len(pc))
for i in po:
    st='M' if (i in mo and i+1 in mo) else '-'
    ctx=' ; '.join(s for _,s in do[max(0,i-1):i+4])
    print(f'{st} o{do[i][0]+0x22a10:x}: {ctx}')
print('--- cand pairs')
inv={v:k for k,v in mo.items()}
for i in pc:
    st='M' if (i in inv and i+1 in inv) else '-'
    ctx=' ; '.join(s for _,s in dc[max(0,i-1):i+4])
    print(f'{st} c{dc[i][0]+0x22a10:x}: {ctx}')
