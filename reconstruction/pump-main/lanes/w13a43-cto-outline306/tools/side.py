#!/usr/bin/env python3
# side.py <orig_fn> <cand_fn> <lo> <hi>: orig insns [lo,hi) (byte addr) with aligned cand insn (or ---)
import sys,re,difflib
def rd(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); t=re.sub(r'^call .*','call',s); t=re.sub(r'lddw (r\d+), .*',r'lddw \1',t); out.append((p[0],s,t))
    return out
o=rd(sys.argv[1]); c=rd(sys.argv[2]); lo=int(sys.argv[3],16); hi=int(sys.argv[4],16)
mp={}
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,[x[2] for x in o],[x[2] for x in c],autojunk=False).get_opcodes():
    if t=='equal':
        for k in range(i2-i1): mp[i1+k]=j1+k
for i,(a,s,_) in enumerate(o):
    if lo<=int(a,16)<hi:
        j=mp.get(i); print(f'{a} {s[:40]:40s} | '+(f'{c[j][0]} {c[j][1][:40]}' if j is not None else '---'))
