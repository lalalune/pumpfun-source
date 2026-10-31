#!/usr/bin/env python3
"""reord.py <src_rx> <name> <spec>: move IR blocks of admin_cto::execute in rx/<src>/m.ll. spec 'a,b,c>d' moves block indices a,b,c before index d (indices from the original order); several specs separated by ';'. Then llc+score via post.py logic."""
import sys,re,os,subprocess
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src,name,spec=sys.argv[1:4]
t=open(f'{OUT}/rx/{src}/m.ll').read()
i=t.index('admin_cto7execute'); i=t.rfind('define',0,i); j=t.index('\n}\n',i); body=t[i:j]
body2=re.sub(r'%(\d+)\b',r'%v\1',body)
blocks=re.split(r'\n(?=[\w.$"-]+:)',body2)
order=list(range(len(blocks)))
for s in spec.split(';'):
    mv,dst=s.split('>'); mv=[int(x) for x in mv.split(',')]; dst=int(dst)
    order=[x for x in order if x not in mv]; k=order.index(dst); order[k:k]=mv
nb='\n'.join(blocks[x] for x in order)
open(f'{OUT}/ed/_reord.py','w').write('EDITS=[lambda t: t.replace(%r,%r)]\n'%(body,nb))
r=subprocess.run(['python3',f'{OUT}/tools/post.py',src,name,f'{OUT}/ed/_reord.py'],capture_output=True,text=True); print(r.stdout.strip(),r.stderr[-500:])
