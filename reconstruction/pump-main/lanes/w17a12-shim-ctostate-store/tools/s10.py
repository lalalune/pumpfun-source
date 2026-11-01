import sys,os,re,json,itertools
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ce2,pscore
ST=['s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
ORIGS=['s_cb','s_hr','s_my','cr','s_ql','s_fc','s_he','s_mf']
def job(a):
    sub,order=a
    if order=='main': seq=['g','fc','cr','mf','my','hr','cb','he']+ST
    elif order=='origst': seq=['g','fc','mf','my','hr','cb','he']+ORIGS
    else: seq=['g','mf','he','fc','cb','hr','my']+ORIGS
    t=ce2.BASE
    i=t.index(ce2.HEAD)+len(ce2.HEAD); j=t.index(ce2.TAIL,i)
    nb=''.join(ce2.vol(ce2.L[k]) if k in sub else ce2.L[k] for k in seq)
    t=t[:i]+nb+t[j:]
    name='%s_%s'%(order,''.join(k[2:4] for k in sub) or 'none')
    r=pscore.score_text(t,name); return r
if __name__=='__main__':
    A=[(set(c),o) for o in ('main','origst','origall') for n in range(0,8) for c in itertools.combinations(ST,n)]
    with Pool(6) as p:
        for r in p.imap_unordered(job,A,chunksize=8): print(json.dumps(r),flush=True)
