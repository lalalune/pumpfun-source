import sys,os,json,itertools
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoedit as C, pscore
LD={'my':['myg','myl'],'hr':['hrg','hrl'],'cb':['cbg','cbl']}
CASH='  %extract.t = icmp ne i8 %i33, 0\n  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n'
USE='  %i169 = zext i1 %cashback.sroa.0.0.off0 to i8\n'
def mk(early,gearly,order,volst,crge,cashl):
    blk=[] if gearly else ['g24','g286']
    if order=='main':
        seq=['fcg','fcl']+([] if crge else ['crg'])+['crm','mfg','mfl']+[x for f in ('my','hr','cb') if f not in early for x in LD[f]]+['heg','hel','s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
    else:
        seq=['mfg','mfl','heg','hel','fcg','fcl']+[x for f in ('cb','hr','my') if f not in early for x in LD[f]]+['s_cb','s_hr','s_my']+([] if crge else ['crg'])+['crm','s_ql','s_fc','s_he','s_mf']
    e=list(early)+(['crg'] if crge else [])
    t=C.build(early=e,block=blk+seq,gearly=gearly,volst=volst)
    if cashl:
        assert t.count(CASH)==1 and t.count(USE)==1
        t=t.replace(CASH,'').replace(USE,CASH+USE)
    return t
def job(a):
    early,gearly,order,volst,crge,cashl=a
    name='E%s_g%d_%s_vs%d_cr%d_cl%d'%(''.join(x[0] for x in early) or '0',gearly,order,volst,crge,cashl)
    try: r=pscore.score_text(mk(*a),name)
    except AssertionError as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    subs=[[],['my'],['cb','hr'],['cb','hr','my']]
    A=[(e,g,o,vs,cr,cl) for e in subs for g in (False,True) for o in ('main','orig') for vs in (False,True) for cr in (False,True) for cl in (False,True) if (cr or cl)]
    with Pool(5) as p:
        R=p.map(job,A)
    R.sort(key=lambda r:-r.get('M',0))
    for r in R: print(json.dumps(r))
