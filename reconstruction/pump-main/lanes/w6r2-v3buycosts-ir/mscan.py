#!/usr/bin/env python3
"""Diagnostic: combinations of code-neutral ops: marker deletions (D<i>) and lifetime-only edge splits (E<j>)."""
import re,subprocess,os,sys,itertools,importlib.util
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w6r2-v3buycosts-ir')
spec=importlib.util.spec_from_file_location('es',OUT+'/bin/escan_lib.py'); es=importlib.util.module_from_spec(spec); spec.loader.exec_module(es)
src=open(OUT+'/irexp/base/fn.ll').read()
lines=src.split('\n')
D=[i for i,l in enumerate(lines) if 'llvm.lifetime' in l and l.strip().startswith('call')]
E=es.edges(src)
def apply(ops):
    dl={D[int(o[1:])] for o in ops if o[0]=='D'}
    f='\n'.join(l for i,l in enumerate(lines) if i not in dl)
    for k,o in enumerate(o for o in ops if o[0]=='E'):
        f=es.split(f,E[int(o[1:])],k)
    return f
def run(name,f):
    p=OUT+'/scan/'+name+'.py'; open(OUT+'/scan/'+name+'.fn','w').write(f)
    open(p,'w').write("def edit(f):\n    return open(%r).read()\n"%(OUT+'/scan/'+name+'.fn'))
    r=subprocess.run(['python3',OUT+'/bin/irexp.py','scan_'+name,p],capture_output=True,text=True)
    os.remove(OUT+'/scan/'+name+'.fn'); os.remove(p)
    import shutil; shutil.rmtree(OUT+'/irexp/scan_'+name,ignore_errors=True)
    return (r.stdout+r.stderr).strip().split('\n')[-1]
def score(r):
    m=re.search(r'bytes=(\d+).*-(\d+) \+(\d+)',r); return (int(m.group(2))+int(m.group(3))) if m else 999
ops=['D%d'%i for i in range(len(D))]+['E%d'%j for j in range(len(E))]
k=int(sys.argv[1]); pref=sys.argv[2].split(',') if len(sys.argv)>2 and sys.argv[2] else []
combos=[c for c in itertools.combinations(ops,k)]
if pref: combos=[tuple(pref)+c for c in combos if not set(c)&set(pref)]
def job(c):
    try: return c,run('m_'+'_'.join(c),apply(c))
    except Exception as e: return c,'ERR '+str(e)[:80]
best=[]
with ThreadPoolExecutor(6) as ex:
    for c,r in ex.map(job,combos,chunksize=4):
        s=score(r)
        if s<=12 and not r.endswith('-9 +11'): print(c,r,flush=True)
        best.append((s,c,r))
best.sort(); print('BEST',best[:5])
