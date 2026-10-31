#!/usr/bin/env python3
"""bwpost.py in_m.ll out_m.ll 'blockregex:w1:w2' ... : add !prof branch_weights to the conditional br terminating each matched
block of execute in a post-opt slimmed module (experiment only)."""
import sys,re
src,dst=sys.argv[1:3]; t=open(src).read()
k=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute17h'); e=t.index('\n}\n',k); b=t[k:e]
B=b.split('\n\n'); md=[]; n0=9000000
for spec in sys.argv[3:]:
    rx,w1,w2=spec.rsplit(':',2)
    hit=0
    for i,x in enumerate(B):
        L=x.split('\n')
        if re.match(rx+r':',L[0]) and L[-1].strip().startswith('br i1'):
            L[-1]=re.sub(r', !prof !\d+','',L[-1])+f', !prof !{n0}'; md.append(f'!{n0} = !{{!"branch_weights", i32 {w1}, i32 {w2}}}'); n0+=1; B[i]='\n'.join(L); hit+=1
    assert hit==1,(spec,hit)
t=t[:k]+'\n\n'.join(B)+t[e:]+'\n'+'\n'.join(md)+'\n'
open(dst,'w').write(t)
