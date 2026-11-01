import sys,os,json,itertools,multiprocessing as mp
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from h1 import *
def addw(t,nid,p):
    a=int(p*2147483647+0.5); b=int((1-p)*2147483647+0.5)
    return t+f'\n!{nid} = !{{!"branch_weights", i32 {a}, i32 {b}}}\n'
def cell(args):
    name,p8,p23,p7,tag=args
    try:
        t=base
        t=addw(addw(addw(t,90001,p8),90002,p23),90003,p7)
        t=h7(t,w8='!90001',w23='!90002')
        t=rep(t,"  br i1 %nh1, label %bb22.i, label %bb16.i, !prof !211\n","  br i1 %nh1, label %bb22.i, label %bb16.i, !prof !90003\n")
        if tag: t=tag1(t)
        r=score(t,name,rg=False)
        import shutil; shutil.rmtree(f'{OUT}/fx/{name}',ignore_errors=True) if r.get('M',0)<2338 else None
        return dict(r,p8=p8,p23=p23,p7=p7,tag=tag)
    except BaseException as e:
        return {'name':name,'err':repr(e)}
if __name__=='__main__':
    P8=[.25,.3,.35,.375,.4,.45,.5,.55,.6,.65]; P23=[.25,.3,.35,.375,.4,.45,.5,.55,.6,.65]; P7=[.51]
    jobs=[(f'g_{i}',a,b,c,tg) for i,(a,b,c,tg) in enumerate(itertools.product(P8,P23,P7,[0,1]))]
    res=[]
    with mp.Pool(3) as pool:
        for r in pool.imap_unordered(cell,jobs):
            res.append(r); open(OUT+'/res/h3.jsonl','a').write(json.dumps(r)+'\n')
    res=[r for r in res if 'M' in r]
    res.sort(key=lambda r:(-r['M'],r['bytes']))
    for r in res[:15]: print({k:r[k] for k in('M','bytes','p8','p23','tag','sig')})
