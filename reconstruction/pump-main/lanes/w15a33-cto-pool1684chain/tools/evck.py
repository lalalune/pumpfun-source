#!/usr/bin/env python3
"""evck.py fn.bin...: event-region colour summary: accounts reload reg(s) between Clock::get and the event emit,
pool_updated reg (stxb [r10-525]), swept source (stxdw [r10-536]), nf source (stxdw [r10-544]), tag reg (and64 rX,255 before jne rX,2)."""
import sys,os,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','tools'))
from bdis import decode
for f in sys.argv[1:]:
    ins=decode(open(f,'rb').read()); T=[d['txt'] for d in ins]
    # event block: find 'stxb [r10-525]'
    k=[i for i,t in enumerate(T) if t.startswith('stxb [r10-525]')]
    if not k: print(f,'no event'); continue
    k=k[-1]; lo=k-80; hi=k+40
    acc=[(hex(ins[i]['off']),T[i].split()[1].rstrip(',')) for i in range(lo,hi) if re.match(r'ldxdw r\d, \[r10-2264\]',T[i])]
    pu=T[k].split(', ')[1]
    def src(sl):
        j=[i for i in range(lo,hi) if T[i].startswith('stxdw [r10-%d]'%sl)]
        if not j: return '?'
        j=j[0]; r=T[j].split(', ')[1]
        # find def of r
        for i in range(j-1,lo,-1):
            if re.match(r'\w+ %s,'%r,T[i]): return r+'<'+T[i]
        return r
    tag=[T[i] for i in range(lo,hi) if re.match(r'and64 r\d, 255',T[i])]
    print(os.path.basename(f), 'acc',acc,'pu',pu,'swept',src(536),'nf',src(544),'old',src(552),'tag',tag)
