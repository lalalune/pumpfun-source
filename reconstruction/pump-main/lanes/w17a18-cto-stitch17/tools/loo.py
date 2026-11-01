#!/usr/bin/env python3
"""loo.py <n commits>: leave-one-out revert genes for the last N first-parent landings that touched admin_cto.rs.
Each gene reverts one landing's changed segment on each changed line (common prefix/suffix trimmed, with context),
applied to the current basecrate text; prints JSON {gene: [(old,new),...]} for genes that apply cleanly."""
import sys,os,subprocess,json
REPO='/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source'
T=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.dirname(T)
F='programs/pump/src/creator/admin_cto.rs'
N=int(sys.argv[1])
log=subprocess.run(['git','-C',REPO,'log','--first-parent','--format=%H %s','-n',str(N),'origin/main','--',F],capture_output=True,text=True).stdout.strip().split('\n')
cur=open(OUT+'/basecrate/src/creator/admin_cto.rs').read()
genes={}
for l in log:
    h,subj=l.split(' ',1)
    pre=subprocess.run(['git','-C',REPO,'show',f'{h}^1:{F}'],capture_output=True,text=True).stdout.split('\n')
    post=subprocess.run(['git','-C',REPO,'show',f'{h}:{F}'],capture_output=True,text=True).stdout.split('\n')
    if len(pre)!=len(post): continue
    eds=[]; ok=True
    for i,(a,b) in enumerate(zip(pre,post)):
        if a==b: continue
        p=0
        while p<min(len(a),len(b)) and a[p]==b[p]: p+=1
        s=0
        while s<min(len(a),len(b))-p and a[len(a)-1-s]==b[len(b)-1-s]: s+=1
        for ctx in (12,24,48,96,200):
            p0=max(0,p-ctx); old=b[p0:len(b)-s+ctx] if s>=ctx else b[p0:]
            new=a[p0:len(a)-s+ctx] if s>=ctx else a[p0:]
            if cur.count(old)==1: break
        else:
            ok=False; break
        eds.append((old,new))
    if not ok or not eds: continue
    # apply jointly to check
    t=cur
    try:
        for o,n in eds:
            assert t.count(o)==1; t=t.replace(o,n)
    except AssertionError: continue
    if t.count('\n')!=cur.count('\n'): continue
    import re
    m=re.search(r'\(#(\d+)\)',subj); key='loo'+(m.group(1) if m else h[:7])
    genes[key]={'eds':eds,'subj':subj[:120]}
json.dump(genes,open(OUT+'/data/loo.json','w'))
for k,v in genes.items(): print(k,len(v['eds']),v['subj'][:100])
