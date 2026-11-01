#!/usr/bin/env python3
"""polflip.py <m.ll (post-opt slim)> <out.jsonl> [workers]: llc-only screen of branch-polarity flips in execute:
br i1 %c, T, F  ->  br i1 %c' , F, T  with %c' the inverted icmp (or xor %c,true). Experiment only."""
import sys,os,re,json,subprocess,hashlib
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,fx
src,outp=sys.argv[1:3]; W=int(sys.argv[3]) if len(sys.argv)>3 else 3
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
cells=[]
for i in range(s,e):
    m=re.match(r'^(\s+)br i1 '+VAL+r', label (%\S+), label (%\S+?)(,.*)?$',L[i])
    if not m: continue
    c=m.group(2); nv='%%pf%d'%i
    new=None
    if c in defs:
        rhs=defs[c][1]; mm=re.match(r'icmp (\w+) (.*)$',rhs)
        if mm and mm.group(1) in INV: new='  %s = icmp %s %s'%(nv,INV[mm.group(1)],mm.group(2))
    if new is None: new='  %s = xor i1 %s, true'%(nv,c)
    br=m.group(1)+'br i1 %s, label %s, label %s%s'%(nv,m.group(4),m.group(3),m.group(5) or '')
    cells.append((i,[new,br]))
OUT=os.environ.get('LANE_OUT',os.path.dirname(T))
done=set()
if os.path.exists(outp):
    for l in open(outp): done.add(json.loads(l)['id'])
def run(cell):
    i,rep=cell; cid='pf:%d'%i
    if cid in done: return
    t='\n'.join(L[:i]+rep+L[i+1:])
    d=os.path.join(OUT,'fx','pf%d'%i); os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(t)
    r=subprocess.run(['nice','-n','5',fx.LLC,*fx.LLCA,d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: res={'id':cid,'err':r.stderr[-300:]}
    else:
        b=oracle.elf_fn(d+'/m.o',oracle.KEEP); M,ratio=fx.Mof(b)
        res={'id':cid,'M':M,'bytes':len(b),'sig':hashlib.sha1(b''.join(oracle.mask(b))).hexdigest()[:12],'src':L[i].strip()[:90]}
    import shutil; shutil.rmtree(d,ignore_errors=True)
    with open(outp,'a') as f: f.write(json.dumps(res)+'\n')
print(len(cells),'cells',flush=True)
with ThreadPoolExecutor(W) as ex: list(ex.map(run,cells))
