#!/usr/bin/env python3
"""and1.py: per-icmp and-1 memory-bool form sweep on post-opt execute (experiment only).
For each `%c = icmp eq|ne i8 %v, 0` that feeds a conditional br of execute, rewrite to `and i8 %v,1` + icmp
(variant a1) and also strip !range from %v's load (variant a1r). Scores like bwx.run."""
import sys,re,json,os
sys.path.insert(0,os.path.dirname(__file__)); import bwx
from concurrent.futures import ThreadPoolExecutor
mod=open(sys.argv[1]).read(); out=open(sys.argv[2],'w'); o=bwx.orig_toks()
pre,fn,post=bwx.split(mod)
conds=sorted({c for _,c,_,_,_ in bwx.brs(mod)})
items=[]
for c in conds:
    m=re.search(r'^(\s*)'+re.escape(c)+r' = icmp (eq|ne) i8 (%[-\w.$"]+), 0\s*$',fn,re.M)
    if m: items.append((c,m))
def go(it):
    c,m=it; res=[]
    for var in ('a1','a1r'):
        ind,pr,v=m.groups(); a=c+'.a1'
        f2=fn.replace(m.group(0),f'{ind}{a} = and i8 {v}, 1\n{ind}{c} = icmp {pr} i8 {a}, 0',1)
        if var=='a1r':
            lm=re.search(r'^(\s*'+re.escape(v)+r' = load i8, [^\n]*?), !range !\d+',f2,re.M)
            if not lm: continue
            f2=f2.replace(lm.group(0),lm.group(1),1)
        r=bwx.run_text(pre+f2+post,o); r.update({'cond':c,'var':var}); res.append(r)
        out.write(json.dumps(r)+'\n'); out.flush()
    return res
with ThreadPoolExecutor(5) as ex: list(ex.map(go,items))
print(len(items))
