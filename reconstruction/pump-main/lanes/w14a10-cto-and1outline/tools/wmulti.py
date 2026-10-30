#!/usr/bin/env python3
"""wmulti.py <post.ll> <name> idx:x:y ...: apply several !prof weights (branch index as in wscan) and score."""
import sys,os,re,subprocess
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src,name=sys.argv[1],sys.argv[2]
L=open(src).read().split('\n')
s=[i for i,l in enumerate(L) if l.startswith('define') and 'admin_cto7execute' in l][0]
e=s+[i for i,l in enumerate(L[s:]) if l=='}'][0]
brs=[i for i in range(s,e) if re.match(r'\s+br i1 %[^,]+, label %[^,]+, label %[^,\s]+$',L[i])]
md=[]
for k,a in enumerate(sys.argv[3:]):
    bi,x,y=map(int,a.split(':')); L[brs[bi]]+=', !prof !%d'%(99990+k); md.append('!%d = !{!"branch_weights", i32 %d, i32 %d}'%(99990+k,x,y))
p=O+'/ir/wm_%s.ll'%name; open(p,'w').write('\n'.join(L)+'\n'+'\n'.join(md)+'\n')
print(subprocess.run(['bash',O+'/tools/pc.sh',name,p],capture_output=True,text=True).stdout)
