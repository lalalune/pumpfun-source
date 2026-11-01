#!/usr/bin/env python3
"""h4.py: on the and-1 base (h1) put the freed 5 pads: 4 stay in bb45.i (312 error block), 1 goes to each block head/tail; llc only; M at 27400."""
import sys,os,json,re,multiprocessing as mp,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from h1 import *
PAD="  %%pad%d = load volatile i8, ptr %%hkx, align 8\n"
def addpad(t,block,where,idx=0):
    F=Fn(t)
    i=F.idx(block); B=F.blocks[i]
    lines=B[1]
    if where=='head':
        # after label and phis
        k=1
        while k<len(lines) and (' = phi ' in lines[k] or lines[k].startswith(';')): k+=1
    else:
        k=len(lines)-1
        while k>0 and not lines[k].startswith('  ') : k-=1
        # before terminator
        while k>0 and not re.match(r'  (br|switch|ret|unreachable)\b',lines[k]): k-=1
    lines.insert(k,(PAD%idx).rstrip('\n'))
    return F.text()
MOD=None
def mod():
    global MOD
    if MOD is None: MOD=baseT()
    return MOD
def baseT():
    t=h7(base)
    if os.environ.get('TAG'): t=tag1(t)
    n=int(os.environ.get('KEEP','4'))
    # add n pads in bb45.i next to the existing ones
    for j in range(n):
        t=addpad(t,'bb45.i','head',100+j)
    return t
def cell(a):
    block,where=a
    name='c_'+re.sub(r'\W','_',block)[:40]+'_'+where
    try:
        t=addpad(mod(),block,where,1)
        r=score(t,name,rg=False); shutil.rmtree(f'{OUT}/fx/{name}',ignore_errors=True)
        return dict(r,block=block,where=where)
    except BaseException as e:
        return {'block':block,'where':where,'err':repr(e)[:200]}
if __name__=='__main__':
    t=mod(); F=Fn(t); names=[b[0] for b in F.blocks]
    r0=score(addpad(t,'bb45.i','head',1),'c_ref',rg=False); print('ref',r0,flush=True)
    jobs=[(n,w) for n in names for w in ('head','tail')]
    outf=OUT+'/res/'+sys.argv[1]
    with mp.Pool(3) as pool:
        for r in pool.imap_unordered(cell,jobs):
            open(outf,'a').write(json.dumps(r)+'\n')
    R=[json.loads(l) for l in open(outf)]
    R=[r for r in R if 'M' in r]; R.sort(key=lambda r:(-r['M'],r['bytes']))
    for r in R[:25]: print(r['M'],r['bytes'],r['block'][:50],r['where'])
