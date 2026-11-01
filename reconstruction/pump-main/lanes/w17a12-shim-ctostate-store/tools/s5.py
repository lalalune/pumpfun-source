import sys,os,json,itertools,random
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoedit as C, pscore
UNITS={'fc':['fcg','fcl'],'cr':['crg','crm'],'mf':['mfg','mfl'],'my':['myg','myl'],'hr':['hrg','hrl'],'cb':['cbg','cbl'],'he':['heg','hel']}
STO=['s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
def job(a):
    perm,sperm=a
    name='L'+''.join(x[0]+x[1] for x in perm)+'_S'+''.join(x[2:4] for x in sperm)
    blk=['g24','g286']+[k for u in perm for k in UNITS[u]]+list(sperm)
    try: r=pscore.score_text(C.build(block=blk),name)
    except AssertionError as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    mode=sys.argv[1]; n=int(sys.argv[2])
    random.seed(int(sys.argv[3]) if len(sys.argv)>3 else 1)
    units=list(UNITS)
    if mode=='L':
        P=list(itertools.permutations(units)); random.shuffle(P); A=[(p,STO) for p in P[:n]]
    else:
        P=list(itertools.permutations(STO)); random.shuffle(P); A=[(['fc','cr','mf','my','hr','cb','he'],p) for p in P[:n]]
    with Pool(5) as p:
        for r in p.imap_unordered(job,A,chunksize=4): print(json.dumps(r),flush=True)
