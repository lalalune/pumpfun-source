import sys,os,json,itertools
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoedit as C, pscore
LD={'my':['myg','myl'],'hr':['hrg','hrl'],'cb':['cbg','cbl']}
def mk(early,gearly,order,volst,volld):
    blk=[] if gearly else ['g24','g286']
    if order=='main':
        seq=['fcg','fcl','crg','crm','mfg','mfl']+[x for f in ('my','hr','cb') if f not in early for x in LD[f]]+['heg','hel','s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
    else:
        seq=['mfg','mfl','heg','hel','fcg','fcl']+[x for f in ('cb','hr','my') if f not in early for x in LD[f]]+['s_cb','s_hr','s_my','crg','crm','s_ql','s_fc','s_he','s_mf']
    return C.build(early=early,block=blk+seq,gearly=gearly,volst=volst,volld=volld)
def job(a):
    early,gearly,order,volst,volld=a
    name='E%s_g%d_%s_vs%d_vl%d'%(''.join(x[0] for x in early) or '0',gearly,order,volst,volld)
    try: r=pscore.score_text(mk(*a),name)
    except AssertionError as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    subs=[[],['my'],['hr'],['cb'],['hr','my'],['cb','my'],['cb','hr'],['cb','hr','my']]
    A=[(e,g,o,vs,vl) for e in subs for g in (False,True) for o in ('main','orig') for vs in (False,True) for vl in (False,True) if not (vl and not e)]
    with Pool(4) as p:
        R=p.map(job,A)
    R.sort(key=lambda r:(-(r.get('bytes')==27400),-r.get('M',0)))
    for r in R: print(json.dumps(r))
