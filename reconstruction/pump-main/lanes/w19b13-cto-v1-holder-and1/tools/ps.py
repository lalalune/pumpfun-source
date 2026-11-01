#!/usr/bin/env python3
"""ps.py <base name> <out.jsonl> '<fixed pads block:where,...>' [--ref m2]: post-opt pad cell scan on fx/<base>/m.ll: each cell adds 1 hkx byte read."""
import sys,os,json,re,multiprocessing as mp,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from po import *
PAD="  %%pad%d = load volatile i8, ptr %%hkx, align 8"
def addpad(t,block,where,idx=0):
    F=Fn(t)
    i=F.idx(block); lines=F.blocks[i][1]
    if where=='head':
        k=1
        while k<len(lines) and (' = phi ' in lines[k] or lines[k].startswith(';')): k+=1
    else:
        k=len(lines)-1
        while k>0 and not re.match(r'  (br|switch|ret|unreachable)\b',lines[k]): k-=1
    lines.insert(k,PAD%idx)
    return F.text()
BT=None; A=None
def init(base,fix):
    global BT
    t=open(f'{OUT}/fx/{base}/m.ll').read()
    t=rename(t) if False else t
    for j,(b,w) in enumerate(fix):
        t=addpad(t,b,w,700+j)
    BT=t
def cell(a):
    block,where=a
    name='c3_'+re.sub(r'\W','_',block)[:40]+'_'+where
    try:
        t=addpad(BT,block,where,1)
        r=score(t,name,rg=False); shutil.rmtree(f'{OUT}/fx/{name}',ignore_errors=True)
        return dict(r,block=block,where=where)
    except BaseException as e:
        return {'block':block,'where':where,'err':repr(e)[:200]}
if __name__=='__main__':
    base=sys.argv[1]; outf=OUT+'/res/'+sys.argv[2]
    fix=[tuple(x.split(':')) for x in sys.argv[3].split(',')] if len(sys.argv)>3 and sys.argv[3] else []
    init(base,fix)
    F=Fn(BT); names=[b[0] for b in F.blocks]
    jobs=[(n,w) for n in names for w in ('head','tail')]
    with mp.Pool(3,initializer=init,initargs=(base,fix)) as pool:
        for r in pool.imap_unordered(cell,jobs):
            open(outf,'a').write(json.dumps(r)+'\n')
    print('done')
