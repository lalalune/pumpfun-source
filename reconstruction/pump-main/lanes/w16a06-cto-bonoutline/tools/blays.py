#!/usr/bin/env python3
"""blays.py <m.s> [n]: block layout with IR names, offsets, sizes, error line imm, terminator."""
import sys,re,os
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import relayn
R=relayn.R
pre,bl,post=R.parse(sys.argv[1]); N=int(sys.argv[2]) if len(sys.argv)>2 else 70
off=0
for n,b in bl[:N]:
    g=re.search(r'#\s*(%\S+)',b[0]); nm=g.group(1) if g else ''
    nm=nm.strip('%"'); nm=nm.split('E.')[-1] if 'to_string' in nm else nm
    ii=R.insns(b); by=sum(16 if b[j].strip().startswith('lddw') else 8 for j in ii)
    errs=[re.search(r'stw \[r10 - \d+\], (\d+)',b[j]) for j in ii]; errs=[e.group(1) for e in errs if e and 280<=int(e.group(1))<=780]
    calls=[b[j].strip().split()[-1][-30:] for j in ii if b[j].strip().startswith('call')]
    last=b[ii[-1]].strip() if ii else ''
    print('%5x %-8s %-22s n=%3d %s %s last=%s'%(off,n,nm[-22:],len(ii),('E'+','.join(errs)) if errs else '',('C:'+','.join(calls)) if calls else '',last[:40]))
    off+=by
