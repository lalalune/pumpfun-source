#!/usr/bin/env python3
"""polpair.py <m.ll> <pf.jsonl> <out.jsonl> [topN]: llc-only pairs/triples of polarity flips whose sizes cancel."""
import sys,os,re,json,subprocess,hashlib,itertools
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fx
src,pff,outp=sys.argv[1:4]; N=int(sys.argv[4]) if len(sys.argv)>4 else 20
L=open(src).read().split('\n')
s=next(i for i,l in enumerate(L) if l.startswith('define') and re.search(r'admin_cto7execute17h',l.split('(')[0]))
e=s
while L[e]!='}': e+=1
VAL=r'(%[\w.$-]+|%"[^"]+")'
defs={}
for i in range(s,e):
    m=re.match(r'^\s+'+VAL+r' = (.*)$',L[i])
    if m: defs[m.group(1)]=(i,m.group(2))
INV={'eq':'ne','ne':'eq','ult':'uge','uge':'ult','ugt':'ule','ule':'ugt','slt':'sge','sge':'slt','sgt':'sle','sle':'sgt'}
def flip(i):
    m=re.match(r'^(\s+)br i1 '+VAL+r', label (%\S+), label (%\S+?)(,.*)?$',L[i])
    c=m.group(2); nv='%%pf%d'%i; new=None
    if c in defs:
        mm=re.match(r'icmp (\w+) (.*)$',defs[c][1])
        if mm and mm.group(1) in INV: new='  %s = icmp %s %s'%(nv,INV[mm.group(1)],mm.group(2))
    if new is None: new='  %s = xor i1 %s, true'%(nv,c)
    return [new,m.group(1)+'br i1 %s, label %s, label %s%s'%(nv,m.group(4),m.group(3),m.group(5) or '')]
R=[json.loads(l) for l in open(pff)]
R=[r for r in R if 'M' in r and r['sig']!='61dcfe87f489']
R.sort(key=lambda r:-r['M']); R=R[:N]
jobs=[]
for k in (2,3):
    for t in itertools.combinations(R,k):
        if sum(r['bytes'] for r in t)!=27400*k: continue
        jobs.append([int(r['id'].split(':')[1]) for r in t])
print(len(jobs),'jobs',flush=True)
OUT=os.environ.get('LANE_OUT',os.path.dirname(T))
def run(ids):
    rep={i:flip(i) for i in ids}
    out=[]
    for i,l in enumerate(L):
        out.extend(rep[i] if i in rep else [l])
    nm='pp'+'_'.join(map(str,ids)); d=os.path.join(OUT,'fx',nm); os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write('\n'.join(out))
    r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'id':nm,'err':r.stderr[-200:]}
    else:
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP); M,_=fx.Mof(b)
        res={'id':nm,'M':M,'bytes':len(b),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12]}
    import shutil; shutil.rmtree(d,ignore_errors=True)
    with open(outp,'a') as f: f.write(json.dumps(res)+'\n')
with ThreadPoolExecutor(3) as ex: list(ex.map(run,jobs))
