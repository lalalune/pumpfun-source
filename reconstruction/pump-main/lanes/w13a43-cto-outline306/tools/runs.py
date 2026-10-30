#!/usr/bin/env python3
# runs.py <orig_fn> <cand_fn> <lo> <hi>: register/frame-blind opcodes in orig range: replace/delete/insert with sizes
import sys,re,difflib
def rd(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); t=re.sub(r'^call .*','call',s); t=re.sub(r'lddw (r\d+), .*',r'lddw \1',t); t=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',t); t=re.sub(r'r\d','r',t); t=re.sub(r'[+-]0x[0-9a-f]+$','J',t) if t.startswith('j') else t
        out.append((p[0],s,t))
    return out
o=rd(sys.argv[1]); c=rd(sys.argv[2]); lo=int(sys.argv[3],16); hi=int(sys.argv[4],16)
for t,i1,i2,j1,j2 in difflib.SequenceMatcher(None,[x[2] for x in o],[x[2] for x in c],autojunk=False).get_opcodes():
    if t=='equal' or not (lo<=int(o[min(i1,len(o)-1)][0],16)<hi): continue
    print(f'{t:7s} orig {o[i1][0] if i1<len(o) else "end"} n={i2-i1:3d} | cand {c[j1][0] if j1<len(c) else "end"} n={j2-j1:3d}')
    for k in range(i1,min(i2,i1+12)): print('   -',o[k][0],o[k][1])
    for k in range(j1,min(j2,j1+12)): print('   +',c[k][0],c[k][1])
