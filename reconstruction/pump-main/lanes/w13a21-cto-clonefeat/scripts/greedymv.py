#!/usr/bin/env python3
"""greedymv.py <module.ll> <scan.jsonl> <out> [rounds] : greedy stacking of movescan edits (llc oracle), size pinned 27,400.
Round r applies the chosen edits plus each candidate that changed code in the single scan; keeps the best at 27,400."""
import sys,re,json,os,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
mod=Path(sys.argv[1]).read_text(); R=[json.loads(l) for l in open(sys.argv[2])]; out=Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
rounds=int(sys.argv[4]) if len(sys.argv)>4 else 3
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); L0=mod[i:j].split('\n')
base=[r for r in R if 'ratio' in r]
# keep only edits that changed code
from collections import Counter
mode=Counter((r['ratio'],r['bytes']) for r in base).most_common(1)[0][0]
cands=[r for r in base if (r['ratio'],r['bytes'])!=mode]
otok,w=co.orig_tokens()
def apply(edits):
    L=list(L0)
    # edits by value name: move def line of v to dest block computed fresh
    for e in edits:
        v=e['v']; kind=e['kind']
        k=[x for x,l in enumerate(L) if re.match(r'  %'+re.escape(v)+r' = ',l)][0]
        line=L[k]
        if kind=='sink':
            pat=re.compile(r'%'+re.escape(v)+r'(?![\w.$-])')
            u=[x for x,l in enumerate(L) if x!=k and pat.search(l)][0]
            b=u
            while not re.match(r'^\S.*:',L[b]): b-=1
            d=b+1
            while re.match(r'  %\S+ = phi ',L[d]): d+=1
            L.pop(k); d=d-1 if k<d else d; L.insert(d,line)
        else:
            tb=e['to']
            b=[x for x,l in enumerate(L) if l.startswith(tb+':')]
            if not b: return None
            b=b[0]+1
            while b<len(L) and L[b].startswith('  '): b+=1
            t=b-1  # terminator line
            L.pop(k); t=t-1 if k<t else t; L.insert(t,line)
    s='\n'.join(L)
    order=[m.group(1) for m in re.finditer(r'^  %(\d+) = ',s,re.M)]
    nums=sorted(order,key=int); mp=dict(zip(order,nums))
    s=re.sub(r'%(\d+)(?![\w.$-])',lambda m:'%__'+mp[m.group(1)] if m.group(1) in mp else m.group(0),s)
    return s.replace('%__','%')
def score(edits,tag):
    s=apply(edits)
    if s is None: return None
    d=out/tag; d.mkdir(exist_ok=True)
    (d/'m.ll').write_text(mod[:i]+s+mod[j:])
    r=subprocess.run(co.LLC+[str(d/'m.ll'),'-filetype=obj','-o',str(d/'m.o')],capture_output=True,text=True)
    res=None
    if not r.returncode:
        ctok,raw,_=co.obj_tokens(d/'m.o',sym); res=co.metrics(otok,ctok,len(raw),w['bytes'])
    for f in ('m.ll','m.o'): (d/f).unlink(missing_ok=True)
    d.rmdir(); return res
chosen=[]; best=None
for rd in range(rounds):
    pool=[c for c in cands if c not in chosen]
    with ThreadPoolExecutor(3) as ex:
        res=list(ex.map(lambda c: (c,score(chosen+[c],f'r{rd}_{c["kind"]}{c["line"]}')),pool))
    ok=[(c,m) for c,m in res if m and m['bytes']==27400]
    if not ok: break
    c,m=max(ok,key=lambda x:x[1]['ratio'])
    if best and m['ratio']<=best['ratio']: break
    chosen.append(c); best=m
    print('round',rd,m,c['kind'],c['v'],c['from'][-40:],'->',c['to'][-40:],flush=True)
json.dump({'chosen':chosen,'best':best},open(out/'greedy.json','w'),indent=1)
