#!/usr/bin/env python3
"""tagdump.py <prefix> lo hi: candidate offsets [lo,hi) with the RAPRIO_TAG asm line (from colmap's <prefix>.s/.bin)."""
import sys,os,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from bdis import decode
pre,lo,hi=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0)
c=open(pre+'.bin','rb').read(); ci=decode(c)
lines=[];f=False;labs=[]
for l in open(pre+'.s'):
    if re.match(r'^_ZN14pump_recovered9admin_cto7execute\w*:',l): f=True; continue
    if f and l.startswith('.Lfunc_end'): break
    if f and re.match(r'^\.?LBB|^\.LBB',l): labs.append(l.strip())
    if f and l.startswith('\t') and not l.startswith('\t.') and not l.startswith('\t#'):
        lines.append((' | '.join(labs), l.strip())); labs=[]
for d,(lab,t) in zip(ci,lines):
    if lo<=d['off']<hi:
        if lab: print('        ',lab)
        print(f"{d['off']:6x}  {t}")
