#!/usr/bin/env python3
"""llw.py <ex.ll> <outdir> <tag> <pattern>:<a>:<b> ... : set branch weights a:b (true:false) on the br following the line matching pattern (regex) in final IR, then xo.sh (llc) + tsites; a=-1 strips existing !prof"""
import sys,os,re,subprocess
src,od,tag=sys.argv[1:4]; T=os.path.dirname(os.path.abspath(__file__))
L=open(src).read().split('\n'); d=f'{od}/{tag}'; os.makedirs(d,exist_ok=True)
for k,e in enumerate(sys.argv[4:]):
    pat,a,b=e.rsplit(':',2); a=int(a); b=int(b)
    n=next(i for i,l in enumerate(L) if re.search(pat,l))
    while not re.match(r'\s*br i1',L[n]): n+=1
    L[n]=re.sub(r', !prof !\d+','',L[n])
    if a>=0: L[n]+=f', !prof !9997{k}'; L.append(f'!9997{k} = !{{!"branch_weights", i32 {a}, i32 {b}}}')
open(d+'/in.ll','w').write('\n'.join(L))
r=subprocess.run([T+'/xo.sh',d+'/in.ll',d],capture_output=True,text=True); print(tag,' '.join(sys.argv[4:]),'|',r.stdout.strip(),r.stderr.strip()[-300:])
os.system(f'cp {d}/in.ll {d}/ex.ll'); os.remove(d+'/in.ll')
print(subprocess.run(['python3',T+'/tsites.py',d],capture_output=True,text=True).stdout.strip())
