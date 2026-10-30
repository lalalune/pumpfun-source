#!/usr/bin/env python3
"""ired.py slim.ll SYM edit.py [blockops...]: apply edit(fn_text)->fn_text to SYM's define, then oracle (block ops X>Y)."""
import sys,os,runpy,subprocess,tempfile
src,sym,ed=sys.argv[1:4]; ops=sys.argv[4:]
t=open(src).read()
L=t.split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and sym in l)
e=next(i for i in range(s,len(L)) if L[i]=='}')
f='\n'.join(L[s:e+1])
if ed!='-':
    f2=runpy.run_path(ed)['edit'](f); assert f2!=f,'edit changed nothing'
else: f2=f
t2='\n'.join(L[:s])+'\n'+f2+'\n'+'\n'.join(L[e+1:])
ME=os.environ.get('MODEDIT')
if ME: t2=runpy.run_path(ME)['edit'](t2)
tag=os.environ.get('TAG','ired')
p=os.path.expanduser(f'~/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle/oracle/{tag}.in.ll'); open(p,'w').write(t2)
os.execvp('python3',['python3',os.path.dirname(__file__)+'/oracle.py',p,sym]+ops)
