# dis.py HARNESS so|orig [lo hi]  -> offsets relative to fn start
import sys,re
H=sys.argv[1]; sys.path.insert(0,H); a=sys.argv[2:]; sys.argv=sys.argv[:1]
import win, coords, score
from pathlib import Path
if a[0]=='orig': st=0x5b3b0; n=18584; p=coords.BASE/'original.so'
else:
    p=Path(a[0]); st,n,_=next(f for f in score.candidate_functions(p) if '8swap_hop17h' in f[2])
d=win.objdump_text(p,st,st+n)
lo=int(a[1],16) if len(a)>1 else 0; hi=int(a[2],16) if len(a)>2 else n
for x in sorted(d):
    if lo<=x-st<=hi: print(hex(x-st), d[x])
