#!/usr/bin/env python3
"""joint.py <fn.bin>... [--k 3] [--minM 2200]: joint splice search over single-clone captures on main.
For every subset (size<=k) whose hunks are disjoint, splice onto main (splice oracle v2) and report M, bytes and the abort
profile (good of 41, TCF good of 25); also an additive-length model for conflicting subsets."""
import sys,os,itertools,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile/tools')
import splice as S
from prof import rel
MAIN=open(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile/an/main.bin'),'rb').read()
B=S.parse(MAIN); BT=S.targets(B)
MC=rel(MAIN)[0]
def good(c): return (sum(1 for x in c if x==0), sum(1 for x in c[:25] if x==0)) if c else (None,None)
def run(files,k=3,minM=0,out=None):
    V=[];names=[]
    for f in files:
        raw=open(f,'rb').read(); v=S.Var(B,raw); c=rel(raw)[0]
        V.append((v,c,S.M(raw),len(raw))); names.append(f.split('/rx/')[-1].replace('/fn.bin',''))
    res=[]
    for r in range(1,k+1):
        for sub in itertools.combinations(range(len(V)),r):
            vs=[V[i][0] for i in sub]
            s=S.splice(MAIN,vs,B,BT)
            if s is None:
                if all(V[i][1] for i in sub):
                    add=[MC[j]+sum(V[i][1][j]-MC[j] for i in sub) for j in range(41)]
                    res.append({'set':[names[i] for i in sub],'conflict':True,'add_good':good(add)})
                continue
            c=rel(s)[0]; m=S.M(s)
            res.append({'set':[names[i] for i in sub],'bytes':len(s),'M':m,'good':good(c),'cum':c})
    res.sort(key=lambda x:-(x.get('M') or 0))
    if out: json.dump(res,open(out,'w'))
    return res
if __name__=='__main__':
    a=sys.argv[1:]; k=3; minM=0; out=None
    if '--k' in a: i=a.index('--k'); k=int(a[i+1]); del a[i:i+2]
    if '--out' in a: i=a.index('--out'); out=a[i+1]; del a[i:i+2]
    res=run(a,k,out=out)
    for r in res[:40]: print(json.dumps({x:y for x,y in r.items() if x!='cum'}))
