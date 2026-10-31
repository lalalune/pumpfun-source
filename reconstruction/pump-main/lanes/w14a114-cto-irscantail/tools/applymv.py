#!/usr/bin/env python3
"""applymv.py <mn.ll> <out.ll> 'u1+u2@p' ...: apply IR block moves, then px2."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import px2
exec(open(T+'/irscan.py').read().split("src,outf=sys.argv")[0])
H,BL,TL=load(open(sys.argv[1]).read())
for s in sys.argv[3:]:
    u,p=s.rsplit('@',1); BL=move(BL,u.split('+'),p)
open(sys.argv[2],'w').write(dump(H,BL,TL)); print(json.dumps(px2.run(sys.argv[2])))
