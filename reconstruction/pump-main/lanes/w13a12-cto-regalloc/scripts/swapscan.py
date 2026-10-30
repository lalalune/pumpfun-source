#!/usr/bin/env python3
"""swapscan.py <module.ll> <outdir> [--par N] [--blocks RE] [--limit N]
llc oracle scan of 'value order' edits in admin_cto::execute: for every adjacent pair of side-effect-free
instructions in a block (load/getelementptr/icmp/select/zext/trunc/binop/extractvalue/insertvalue, no
lifetime/store/call), where the second does not use the first, swap them, llc, and score.
Writes outdir/scan.jsonl (one row per edit). Experiment-only (IR edits are not proposals)."""
import sys,re,json,os,subprocess,difflib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
a=sys.argv; mod=Path(a[1]).read_text(); out=Path(a[2]); out.mkdir(parents=True,exist_ok=True)
par=int(a[a.index('--par')+1]) if '--par' in a else 3
bre=re.compile(a[a.index('--blocks')+1]) if '--blocks' in a else None
lim=int(a[a.index('--limit')+1]) if '--limit' in a else 10**9
sym=co.SYMRE.search(mod).group(0); i,j=co.fn_bounds(mod,sym); fn=mod[i:j]; L=fn.split('\n')
PURE=re.compile(r'^  %([\w.$"-]+) = (load|getelementptr|icmp|select|zext|sext|trunc|and|or|xor|add|sub|shl|lshr|ashr|mul|extractvalue|insertvalue|bitcast|ptrtoint|inttoptr) ')
cands=[]; blk=None
for k,l in enumerate(L):
    m=re.match(r'^([\w.$"-]+):',l)
    if m: blk=m.group(1); continue
    if bre and (blk is None or not bre.search(blk)): continue
    if k+1>=len(L): break
    m1=PURE.match(l); m2=PURE.match(L[k+1])
    if not (m1 and m2): continue
    if re.search(r'%'+re.escape(m1.group(1))+r'\b',L[k+1]): continue
    cands.append((k,blk,m1.group(1),m2.group(1)))
cands=cands[:lim]
otok,w=co.orig_tokens()
def one(c):
    k,blk,x,y=c
    L2=list(L); L2[k],L2[k+1]=L2[k+1],L2[k]
    if x.isdigit() and y.isdigit():
        s='\n'.join(L2)
        s=re.sub(r'%'+x+r'\b','%__TMP__',s); s=re.sub(r'%'+y+r'\b','%'+x,s); s=s.replace('%__TMP__','%'+y)
        L2=s.split('\n')
    d=out/f'w{k}'; d.mkdir(exist_ok=True)
    (d/'m.ll').write_text(mod[:i]+'\n'.join(L2)+mod[j:])
    r=subprocess.run(co.LLC+[str(d/'m.ll'),'-filetype=obj','-o',str(d/'m.o')],capture_output=True,text=True)
    row={'line':k,'block':blk,'a':x,'b':y}
    if r.returncode: row['err']=r.stderr[-200:]
    else:
        ctok,raw,_=co.obj_tokens(d/'m.o',sym); row.update(co.metrics(otok,ctok,len(raw),w['bytes']))
    for f in ('m.ll','m.o'): (d/f).unlink(missing_ok=True)
    d.rmdir()
    return row
print('candidates',len(cands),flush=True)
with ThreadPoolExecutor(par) as ex, open(out/'scan.jsonl','a') as f:
    for row in ex.map(one,cands):
        f.write(json.dumps(row)+'\n'); f.flush()
