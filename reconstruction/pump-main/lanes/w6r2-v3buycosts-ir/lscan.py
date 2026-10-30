#!/usr/bin/env python3
"""Diagnostic: delete each lifetime marker (singly) in v3_buy_costs IR and report the llc diff vs original."""
import re,subprocess,os,sys
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w6r2-v3buycosts-ir')
lines=open(OUT+'/irexp/base/fn.ll').read().split('\n')
idx=[i for i,l in enumerate(lines) if 'llvm.lifetime' in l and l.strip().startswith('call')]
print(len(idx),'markers')
def run(name,keep):
    f='\n'.join(l for i,l in enumerate(lines) if i not in keep)
    p=OUT+'/scan/'+name+'.py'
    open(OUT+'/scan/'+name+'.fn','w').write(f)
    open(p,'w').write("def edit(f):\n    return open(%r).read()\n"%(OUT+'/scan/'+name+'.fn'))
    r=subprocess.run(['python3',OUT+'/bin/irexp.py','scan_'+name,p],capture_output=True,text=True)
    return (r.stdout+r.stderr).strip().split('\n')[-1]
mode=sys.argv[1] if len(sys.argv)>1 else 'single'
if mode=='single':
    for i in idx:
        print(i, lines[i].strip()[:70], '=>', run('d%d'%i,{i}))
if mode=='pairs':
    import itertools
    from concurrent.futures import ThreadPoolExecutor
    pairs=list(itertools.combinations(idx,2))
    def job(p): return p, run('p%d_%d'%p,set(p))
    with ThreadPoolExecutor(6) as ex:
        for p,r in ex.map(job,pairs):
            m=re.search(r'bytes=(\d+).*-(\d+) \+(\d+)',r)
            if m and (int(m.group(2))<9 or m.group(1)=='2120'): print(p,r,flush=True)
if mode=='set':
    s=set(int(x) for x in sys.argv[2].split(','))
    print(run('s'+'_'.join(map(str,sorted(s))),s))
