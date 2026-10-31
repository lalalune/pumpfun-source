#!/usr/bin/env python3
"""insmv.py <mn.ll> <out.ll> '<exact instr text>@<line idx in block>|<+N>' ...: move an instruction line within its block. px2."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
H,BL,TL=load(open(sys.argv[1]).read())
for spec in sys.argv[3:]:
    txt,t=spec.rsplit('@',1)
    hits=[(bi,k) for bi,b in enumerate(BL) for k,l in enumerate(b[1]) if l.strip().startswith(txt)]
    assert len(hits)==1,(txt,len(hits)); bi,k=hits[0]; L=list(BL[bi][1]); x=L[k]
    if t.startswith('='):  # before the line starting with text
        tt=t[1:]; t=[j for j,l in enumerate(L) if l.strip().startswith(tt)]; assert len(t)==1,(tt,t); t=t[0]
    else: t=int(t)
    if t<k: L=L[:t]+[x]+L[t:k]+L[k+1:]
    else: L=L[:k]+L[k+1:t]+[x]+L[t:]
    BL[bi]=[BL[bi][0],L]
open(sys.argv[2],'w').write(dump(H,BL,TL)); print(json.dumps(px2.run(sys.argv[2])))
