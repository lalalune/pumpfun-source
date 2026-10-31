#!/usr/bin/env python3
"""side.py <name> lo hi : orig insns in [lo,hi) offset, beside cand rx/<name> aligned (opcodes diff)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
D=os.path.dirname(T)
o=g['mask'](g['orig_window']()); oi=[l.split(None,1)[1] for l in open(D+'/orig.txt')]
n=sys.argv[1]; lo,hi=int(sys.argv[2],16),int(sys.argv[3],16)
c=g['mask'](open(D+'/rx/'+n+'/fn.bin','rb').read()); ci=[l.strip() for l in open(D+'/rx/'+n+'/dis.txt')]
# addr offsets
oa=[];a=0
for t in o: oa.append(a); a+=len(t)
sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if (oa[i1] if i1<len(oa) else 1e9) >= hi: break
    if i2>0 and oa[i2-1]<lo: continue
    if tag=='equal':
        print('   == %d insns  orig %#x..  cand %d..'%(i2-i1,oa[i1],j1)); continue
    L=max(i2-i1,j2-j1)
    for k in range(L):
        a=oi[i1+k] if i1+k<i2 else ''; b=ci[j1+k] if j1+k<j2 else ''
        print('%6s %-36s | %s'%(hex(oa[i1+k]) if i1+k<i2 else '',a[:36],b))
