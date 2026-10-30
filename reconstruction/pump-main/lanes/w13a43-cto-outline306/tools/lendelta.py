#!/usr/bin/env python3
# lendelta.py <orig_fn> <cand_fn> [bin]: per orig-address bin, orig insns minus aligned cand insns (positive = original longer there)
import sys,re,difflib
def toks(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s); s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'r\d','r',s); out.append(s)
    return out
o=toks(sys.argv[1]); c=toks(sys.argv[2]); bn=int(sys.argv[3]) if len(sys.argv)>3 else 100
d=[0.0]*(len(o)//bn+2)
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,o,c,autojunk=False).get_opcodes():
    if t=='equal': continue
    n=i2-i1; m=j2-j1
    if n: 
        for i in range(i1,i2): d[i//bn]+=1-m/n
    else: d[min(i1,len(o)-1)//bn]-=m
for k,v in enumerate(d):
    if abs(v)>=3: print(f'{k*bn*8:#07x} {v:+.0f}')
