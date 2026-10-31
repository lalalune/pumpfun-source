#!/usr/bin/env python3
"""bwprobe.py <m.ll> '<br line exact>' a:b ... : attach branch_weights to one br in a slim module, print free cells (IR probe only)."""
import sys,subprocess,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray'
m,br=sys.argv[1],sys.argv[2]; t=open(m).read(); assert t.count(br+'\n')==1,t.count(br+'\n')
env=dict(os.environ)
for ab in sys.argv[3:]:
    a,b=ab.split(':'); d=f'{O}/tmp/bw_{a}_{b}'; os.makedirs(d,exist_ok=True)
    s=t.replace(br+'\n',br+', !prof !99999\n')+f'\n!99999 = !{{!"branch_weights", i32 {a}, i32 {b}}}\n'
    open(d+'/m.ll','w').write(s)
    r=subprocess.run(['bash',O+'/tools/cellf.sh',d+'/m.ll',d],capture_output=True,text=True,env=env)
    print(ab,(r.stdout.strip() or r.stderr[-300:]).split('\n')[-1],flush=True)
