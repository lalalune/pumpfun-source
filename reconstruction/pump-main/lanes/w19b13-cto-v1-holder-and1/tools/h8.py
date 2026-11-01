#!/usr/bin/env python3
"""h8.py <out.jsonl> '<fixed pads: block:where,...>' : greedy pad round at pinned size on tag1+h7; each cell adds 1 pad"""
import sys,os,json,re,multiprocessing as mp,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
os.environ['KEEP']='0'
from h4 import *
FIX=[tuple(x.split(':')) for x in sys.argv[2].split(',')] if len(sys.argv)>2 and sys.argv[2] else []
BT=None
def B2():
    t=tag1(h7(base))
    for j,(b,w) in enumerate(FIX):
        t=addpad(t,b,w,200+j)
    return t
def cell2(a):
    global BT
    if BT is None: BT=B2()
    block,where=a
    name='c2_'+re.sub(r'\W','_',block)[:40]+'_'+where
    try:
        t=addpad(BT,block,where,1)
        r=score(t,name,rg=False); shutil.rmtree(f'{OUT}/fx/{name}',ignore_errors=True)
        return dict(r,block=block,where=where)
    except BaseException as e:
        return {'block':block,'where':where,'err':repr(e)[:200]}
if __name__=='__main__':
    t=B2(); F=Fn(t); names=[b[0] for b in F.blocks]
    jobs=[(n,w) for n in names for w in ('head','tail')]
    outf=OUT+'/res/'+sys.argv[1]
    with mp.Pool(3) as pool:
        for r in pool.imap_unordered(cell2,jobs):
            open(outf,'a').write(json.dumps(r)+'\n')
    print('done')
