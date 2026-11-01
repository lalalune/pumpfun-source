#!/usr/bin/env python3
"""h5.py <out.jsonl>: on the and-1 base: scan post-opt !prof on every conditional br x ratios (llc only). Reports M, bytes."""
import sys,os,json,re,multiprocessing as mp,shutil
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from h1 import *
RATIOS=[.02,.1,.2,.3,.375,.45,.49,.5,.51,.55,.625,.7,.8,.9,.98]
def B():
    t=h7(base)
    if os.environ.get('TAG'): t=tag1(t)
    return t
MOD=None
def brs(t):
    F=Fn(t); out=[]
    for b in F.blocks:
        for i,l in enumerate(b[1]):
            if re.match(r'  br i1 ',l): out.append((b[0],i,l))
    return out
def cell(a):
    global MOD
    if MOD is None:
        MOD=B()
    block,i,p=a
    name='w_'+re.sub(r'\W','_',block)[:30]+f'_{int(p*1000)}'
    try:
        F=Fn(MOD); L=F.blk(block)[1]; l=L[i]
        l2=re.sub(r', !prof !\d+','',l)
        nid=90010
        L[i]=l2+f', !prof !{nid}'
        x=int(p*2147483647+0.5); y=int((1-p)*2147483647+0.5)
        t=F.text()+f'\n!{nid} = !{{!"branch_weights", i32 {x}, i32 {y}}}\n'
        r=score(t,name,rg=False); shutil.rmtree(f'{OUT}/fx/{name}',ignore_errors=True)
        return {'M':r.get('M'),'bytes':r.get('bytes'),'sig':r.get('sig'),'block':block,'p':p,'br':l.strip()[:70]}
    except BaseException as e:
        return {'block':block,'p':p,'err':repr(e)[:200]}
if __name__=='__main__':
    t=B(); L=brs(t); print(len(L),'brs',flush=True)
    jobs=[(b,i,p) for b,i,_ in L for p in RATIOS]
    outf=OUT+'/res/'+sys.argv[1]
    with mp.Pool(3) as pool:
        for r in pool.imap_unordered(cell,jobs):
            open(outf,'a').write(json.dumps(r)+'\n')
    print('done',flush=True)
