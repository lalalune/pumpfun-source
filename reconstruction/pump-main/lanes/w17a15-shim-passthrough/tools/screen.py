#!/usr/bin/env python3
"""screen.py <base.ll> <edits.jsonl> <out.jsonl> [workers] [kinds] [--combo file]: score single edits (or combos) with fx."""
import sys,os,json,time
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import fx
EXTRA=['!990001 = !{!"branch_weights", i32 2000, i32 1}','!990002 = !{!"branch_weights", i32 1, i32 2000}']
_DECL={}
def apply(L,edits):
    rep={}; extra=list(EXTRA)
    for e in edits:
        for k,v in e['rep'].items():
            k=int(k)
            if k in rep: return None
            rep[k]=v
        extra+=e.get('extra',[])
    out=[]
    for i,l in enumerate(L):
        if i in rep: out.extend(rep[i])
        else: out.append(l)
    seen=set(); ex2=[]
    import re as _re
    have=_DECL.get(id(L))
    if have is None:
        have=set(_re.findall(r'^declare [^@]*(@[\w.$-]+)\(',chr(10).join(x for x in L if x.startswith('declare')),_re.M)); _DECL[id(L)]=have
    for x in extra:
        m=_re.match(r'^declare [^@]*(@[\w.$-]+)\(',x)
        if m and m.group(1) in have: continue
        if x not in seen: seen.add(x); ex2.append(x)
    return '\n'.join(out+ex2)+'\n'
def main():
    a=sys.argv[1:]; base,ef,outf=a[0],a[1],a[2]; W=int(a[3]) if len(a)>3 else 3
    kinds=a[4].split(',') if len(a)>4 and a[4]!='-' else None
    L=open(base).read().split('\n')
    E={}
    for l in open(ef):
        e=json.loads(l); E[e['id']]=e
    done=set()
    if os.path.exists(outf):
        for l in open(outf):
            try: done.add(json.loads(l)['id'])
            except Exception: pass
    if '--combo' in a:
        jobs=[]
        for l in open(a[a.index('--combo')+1]):
            ids=l.split()
            if ids and '+'.join(ids) not in done: jobs.append(ids)
    else:
        jobs=[[i] for i,e in E.items() if i not in done and (kinds is None or e['kind'] in kinds or e['kind']+':'+e['cls'] in kinds)]
        if kinds:
            pri={k:n for n,k in enumerate(kinds)}
            jobs.sort(key=lambda j:pri.get(E[j[0]]['kind']+':'+E[j[0]]['cls'],pri.get(E[j[0]]['kind'],99)))
    print(len(jobs),'jobs',flush=True)
    def run(ids):
        t=apply(L,[E[i] for i in ids])
        if t is None: r={'id':'+'.join(ids),'err':'conflict'}
        else:
            nm='s'+str(abs(hash('+'.join(ids)))%10**9)
            r=fx.run(t,nm); r['id']='+'.join(ids); r.pop('name',None)
            try:
                import shutil; shutil.rmtree(os.path.join(fx.OUT,'fx',nm))
            except Exception: pass
        with open(outf,'a') as f: f.write(json.dumps(r)+'\n')
        return r
    with ThreadPoolExecutor(W) as ex: list(ex.map(run,jobs))
if __name__=='__main__': main()
