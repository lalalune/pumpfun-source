#!/usr/bin/env python3
"""fl.py <name> [--ir base.ll edits.py]: flag-colour screen of rx/<name>/m.ll (experiment only).
With --ir: rx/<name>/m.ll = base.ll with EDITS (exact single-occurrence replacements) applied first.
Finds the holder-flag spill slot (the LDD_V1 %stack.N feeding the STB to curve+165), runs the SSC oracle natural and with
the flag forced deepest (weight 5e-4) and at a few other weights; writes rx/<name>/fl.json, fn.bin, f.o, pei.mir."""
import sys,os,json,re,subprocess,runpy,shutil
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import flagcol as F, oracle
OUT=os.path.dirname(T); LLC=OUT+'/llvmb/bin/llc'; A=F.A
a=sys.argv[1:]; name=a.pop(0); d=f'{OUT}/rx/{name}'; os.makedirs(d,exist_ok=True)
if a and a[0]=='--ir':
    base,ed=a[1],a[2]; t=open(base).read()
    for x,y in runpy.run_path(ed)['EDITS']:
        c=t.count(x); assert c==1,(c,x[:150]); t=t.replace(x,y)
    open(d+'/m.ll','w').write(t)
ll=d+'/m.ll'
p=subprocess.run([LLC,*A,ll,'-stop-before=stack-slot-coloring','-o',d+'/pressc.mir'],capture_output=True,text=True)
if p.returncode: print(json.dumps({'name':name,'err':p.stderr[-500:]})); sys.exit(1)
mir=open(d+'/pressc.mir').read().split('\n')
flag=None; cands=[]
for i,l in enumerate(mir):
    m=re.match(r'\s+STB_V1 killed \$(r\d), killed \$(r\d), 165\b',l)
    if m:
        for j in range(i-1,max(i-6,0),-1):
            mm=re.match(r'\s+\$%s = LDD_V1 %%stack\.(\d+), 0\s*$'%m.group(1),mir[j])
            if mm: cands.append(int(mm.group(1))); break
            if re.match(r'\s+\$%s = '%m.group(1),mir[j]): cands.append(('reg',mir[j].strip()[:60])); break
flag=next((c for c in cands if isinstance(c,int)),None)
subprocess.run([LLC,*A,ll,'-stop-after=prologepilog','-o',d+'/pei.mir'],capture_output=True)
subprocess.run([LLC,*A,ll,'-filetype=obj','-o',d+'/f.o'],capture_output=True)
b=oracle.elf_fn(d+'/f.o',oracle.KEEP); open(d+'/fn.bin','wb').write(b)
w=[flag] if flag else []
res={'name':name,'flag':flag,'cands':cands}
specs=['-']+([f'{flag}:=0.0005',f'{flag}:=0.01',f'{flag}:=0.2'] if flag else [])
rows=[]
for s in specs:
    r=F.run(ll,s,w)
    r=r[0] if isinstance(r,tuple) else r
    rows.append(r)
res['rows']=rows
json.dump(res,open(d+'/fl.json','w'))
nat=rows[0]; deep=rows[1] if len(rows)>1 else {}
fk=lambda r:(r.get(f'SS{flag}') or {}).get('off') if flag else None
print(json.dumps({'name':name,'flag':flag,'bytes':nat.get('bytes'),'M':nat.get('M'),'ratio':nat.get('ratio'),'flag_off':fk(nat),'ncol':nat.get('ncol'),
  'M_deep':deep.get('M'),'M_w01':rows[2].get('M') if len(rows)>2 else None,'off_w01':fk(rows[2]) if len(rows)>2 else None,'M_w2':rows[3].get('M') if len(rows)>3 else None,'off_w2':fk(rows[3]) if len(rows)>3 else None}))
