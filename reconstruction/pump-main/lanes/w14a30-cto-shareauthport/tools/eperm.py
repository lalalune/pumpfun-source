#!/usr/bin/env python3
"""eperm.py <mn.ll> <ptrvar e.g. %_161> <out.jsonl>: permute the 6 scalar reads that directly follow `ptrvar = load` (key,owner,rent,f40,f41,f42)."""
import sys,os,re,subprocess,json,itertools,tempfile
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); g={}; exec(open(T+'/rx.py').read().split("OUT=os.environ")[0],g)
ORIG=g['orig_window'](); mll,X,out=sys.argv[1:4]
L=open(mll).read().split('\n'); xi=next(i for i,l in enumerate(L) if l.startswith('  '+X+' = load'))
F={'key':[xi+1]}; i=xi+2
for nm in ('owner','rent','f40','f41','f42'):
    off={'owner':24,'rent':32,'f40':40,'f41':41,'f42':42}[nm]
    j=next(k for k in range(xi,xi+20) if L[k].endswith('ptr '+X+', i64 %d'%off)); F[nm]=[j,j+1]
rows=sorted(i for v in F.values() for i in v); lo,hi=rows[0],rows[-1]; assert hi-lo==10,(lo,hi)
cur=sorted(F,key=lambda n:F[n][0])
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
def run(pm):
    body=[L[i] for n in pm for i in F[n]]; t='\n'.join(L[:lo]+body+L[hi+1:])
    d=tempfile.mkdtemp(dir=os.path.dirname(os.path.abspath(out))); open(d+'/m.ll','w').write(t)
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: subprocess.run(['rm','-rf',d]); return {'lab':'.'.join(pm),'err':r.stderr[-200:]}
    c=g['elf_fn'](d+'/m.o',g['KEEP']); rr,sd=g['metric'](c,ORIG); subprocess.run(['rm','-rf',d])
    return {'lab':'.'.join(pm),'ratio':round(rr,5),'bytes':len(c),'slots':sd}
print('current','.'.join(cur),file=sys.stderr)
with ThreadPoolExecutor(3) as ex, open(out,'w') as f:
    for r in ex.map(run,itertools.permutations(cur)): f.write(json.dumps(r)+'\n'); f.flush()
