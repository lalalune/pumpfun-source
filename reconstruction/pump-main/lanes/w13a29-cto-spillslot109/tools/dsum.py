#!/usr/bin/env python3
"""dsum.py <cand> [lo hi]: per orig slot, majority delta (orig-cand) of aligned accesses; compressed into runs."""
import sys,re,subprocess,collections
lo=sys.argv[2] if len(sys.argv)>2 else '0x0'; hi=sys.argv[3] if len(sys.argv)>3 else '0xc40'
out=subprocess.run([sys.executable,__file__.replace('dsum.py','smap.py'),sys.argv[1],lo,hi,'o'],capture_output=True,text=True).stdout
runs=[]
for l in out.splitlines():
    f,*acc=l.split(); f=int(f,16)
    c=collections.Counter(int(a.split('>')[1],16) for a in acc if not a.endswith('>-'))
    d=(f-c.most_common(1)[0][0]) if c else None
    if runs and runs[-1][2]==d and f-runs[-1][1]<=8: runs[-1][1]=f
    else: runs.append([f,f,d])
print(' '.join('%x-%x:%s'%(a,b,d) for a,b,d in runs))
