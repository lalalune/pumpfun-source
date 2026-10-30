#!/usr/bin/env python3
"""bwscan.py <m.ll> <outdir> [--par N] [--only re]: diagnostic llc oracle scan for the clone-run RA (experiment only).
For every conditional branch in admin_cto::execute, sets branch weights 1:2000 and 2000:1 (block frequency only)
and reports plain ratio, bytes and clonefeat spill/reg. Shows which block frequencies decide whether the
accounts pointer is region-split into a register across the sharing-CPI clone run."""
import sys,re,json,os,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, clonefeat, difflib
a=sys.argv; mod=Path(a[1]).read_text(); out=Path(a[2]); out.mkdir(parents=True,exist_ok=True)
par=int(a[a.index('--par')+1]) if '--par' in a else 4
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); fn=mod[i:j]; L=fn.split('\n')
otok,w=co.orig_tokens()
BR=re.compile(r'^(  br i1 [^,]+, label %[\w.$"-]+, label %[\w.$"-]+)(, !prof ![0-9]+)?(.*)$')
cands=[]
for k,l in enumerate(L):
    m=BR.match(l)
    if m:
        for wt in ('1, 2000','2000, 1'): cands.append((k,wt))
MD='\n!9999901 = !{!"branch_weights", i32 1, i32 2000}\n!9999902 = !{!"branch_weights", i32 2000, i32 1}\n'
def one(c):
    k,wt=c; tag=f'bw{k}_{"lo" if wt.startswith("1,") else "hi"}'
    d=out/tag; d.mkdir(exist_ok=True)
    m=BR.match(L[k]); L2=list(L); L2[k]=m.group(1)+(', !prof !9999901' if wt.startswith('1,') else ', !prof !9999902')+m.group(3)
    (d/'m.ll').write_text(mod[:i]+'\n'.join(L2)+mod[j:]+MD)
    r=subprocess.run(co.LLC+[str(d/'m.ll'),'-filetype=obj','-o',str(d/'m.o')],capture_output=True,text=True)
    (d/'m.ll').unlink()
    if r.returncode: return {'tag':tag,'err':r.stderr[-200:]}
    ct,raw,_=co.obj_tokens(d/'m.o',sym); (d/'m.o').unlink()
    s,rg=clonefeat.feats(ct)
    res={'tag':tag,'line':k,'br':L[k].strip()[:90],'bytes':len(raw),'cf':f'{s}/{rg}'}
    if s>=3: res['ratio']=round(difflib.SequenceMatcher(None,otok,ct,autojunk=False).ratio(),5)
    return res
with ThreadPoolExecutor(par) as ex, open(out/'res.jsonl','a') as f:
    for r in ex.map(one,cands):
        f.write(json.dumps(r)+'\n'); f.flush()
        if r.get('cf','0/0').split('/')[0] not in ('2',): print(json.dumps(r),flush=True)
