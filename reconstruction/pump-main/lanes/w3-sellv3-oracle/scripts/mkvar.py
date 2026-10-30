#!/usr/bin/env python3
# mkvar.py <trial> <edits.py>   edits.py defines EDITS=[(old,new),...] applied to src/trade_v3.rs (or FILE->list via FILES dict)
import sys,shutil,os,runpy
WT=os.environ.get("BASESRC","/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-sellv3-oracle/programs/pump")
OUT=os.path.expanduser("~/.cache/pumpfun-reconstruction/lanes/w3-sellv3-oracle")
t=sys.argv[1]; d=f"{OUT}/src/{t}"
if os.path.exists(d): shutil.rmtree(d)
shutil.copytree(WT,d,ignore=shutil.ignore_patterns('target'))
ns=runpy.run_path(sys.argv[2])
files=ns.get('FILES',{'src/trade_v3.rs':ns.get('EDITS',[])})
for f,eds in files.items():
    p=f"{d}/{f}"; s=open(p).read()
    for o,n in eds:
        c=s.count(o)
        if c!=1: shutil.rmtree(d); sys.exit(f"edit not unique ({c}): {o[:80]}")
        if o.count('\n')!=n.count('\n'): print("WARN line count change",o[:60])
        s=s.replace(o,n)
    open(p,'w').write(s)
print(d)
