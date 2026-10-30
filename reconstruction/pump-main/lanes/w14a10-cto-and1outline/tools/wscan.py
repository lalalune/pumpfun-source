#!/usr/bin/env python3
"""wscan.py <post.ll> <tag>: for each conditional br in execute, try !prof weights (20:12, 12:20, 1:1000, 1000:1); print improvements."""
import sys,os,re,subprocess,json
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src,tag=sys.argv[1],sys.argv[2]
t=open(src).read(); L=t.split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
e=s+[i for i,l in enumerate(L[s:]) if l=='}'][0]
brs=[i for i in range(s,e) if re.match(r'\s+br i1 %[^,]+, label %[^,]+, label %[^,\s]+$',L[i])]
print(len(brs),'branches',file=sys.stderr)
W=[('a',20,12),('b',12,20),('c',1,1000),('d',1000,1)]
res=[]
for bi,i in enumerate(brs):
    for nm,x,y in W:
        L2=L[:]; L2[i]=L[i]+', !prof !99999'
        t2='\n'.join(L2)+'\n!99999 = !{!"branch_weights", i32 %d, i32 %d}\n'%(x,y)
        p=O+'/ir/ws_%s.ll'%tag; open(p,'w').write(t2)
        r=subprocess.run(['python3',O+'/tools/llcm.py','ws_'+tag,p],capture_output=True,text=True)
        try: d=json.loads(r.stdout.strip().splitlines()[-1])
        except: continue
        res.append((d['ratio'],d['bytes'],bi,nm,L[i].strip()[:80]))
res.sort(reverse=True)
for r in res[:25]: print(r)
json.dump(res,open(O+'/ws_%s.json'%tag,'w'))
