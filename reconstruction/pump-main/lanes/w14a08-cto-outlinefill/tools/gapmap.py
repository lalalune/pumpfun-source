#!/usr/bin/env python3
# gapmap.py <orig_fn> <cand_fn> <lo> <hi>: unmatched runs (frame+reg masked tokens) with orig/cand addresses
import sys,re,difflib
def rd(f):
    A=[];T=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'\br\d\b','r',s)
        A.append(p[1].strip()); T.append(s)
    return A,T
oa,o=rd(sys.argv[1]); ca,c=rd(sys.argv[2]); lo,hi=int(sys.argv[3],16)//8,int(sys.argv[4],16)//8
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,o,c,autojunk=False).get_opcodes():
    if t=='equal' or i2<lo or i1>hi: continue
    print(f'--- {t} orig {i1*8:#x}+{i2-i1} cand {j1*8:#x}+{j2-j1}')
    for i in range(i1,min(i2,i1+12)): print('  O',oa[i])
    for j in range(j1,min(j2,j1+12)): print('  C',ca[j])
