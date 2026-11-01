import sys,os,json,itertools
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoedit as C, pscore, s3
H4='  %i44 = and i8 %arg, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %i44, 0\n'
CASH=s3.CASH
B6='bb6.i:                                            ; preds = %bb11\n'
def mk(early,gearly,order,volst,crge,cashl,hl,and1):
    t=s3.mk(early,gearly,order,volst,crge,cashl)
    h=H4.replace('and i8 %arg, -3','and i8 %arg, 1').replace('icmp eq i8 %i44, 0','icmp eq i8 %i44, 0') if and1 else H4
    if and1: h=h  # (x&1)==0  <=> not Some(true)
    mv=h+('' if cashl else CASH)
    assert t.count(H4)==1
    if hl:
        if not cashl:
            assert t.count(H4+CASH)==1; t=t.replace(H4+CASH,'')
        else: t=t.replace(H4,'')
        t=t.replace(B6,B6+mv)
    else:
        t=t.replace(H4,h)
    return t
def job(a):
    name='E%s_g%d_%s_vs%d_cr%d_cl%d_hl%d_a%d'%((''.join(x[0] for x in a[0]) or '0',)+tuple(int(x) if isinstance(x,bool) else x for x in a[1:]))
    try: r=pscore.score_text(mk(*a),name)
    except AssertionError as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    subs=[[],['cb','hr','my'],['cb','hr']]
    A=[(e,g,o,vs,cr,cl,hl,a1) for e in subs for g in (False,True) for o in ('main','orig') for vs in (False,True) for cr in (False,) for cl in (False,) for hl in (False,True) for a1 in (False,True) if (hl or a1)]
    with Pool(5) as p: R=p.map(job,A)
    R.sort(key=lambda r:-r.get('M',0))
    for r in R: print(json.dumps(r))
