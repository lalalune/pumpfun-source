import sys,os,json,itertools,random
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ce2, pscore
ST=['s_mf','s_my','s_hr','s_cb','s_ql','s_he','s_fc']
def job(a):
    perm,vs,crpos=a
    seq=['g','fc','mf','my','hr','cb','he']
    st=list(perm); st.insert(crpos,'cr')
    name='S'+''.join(x[2:4] if x!='cr' else 'CR' for x in st)+'_v%d'%vs
    try: r=pscore.score_text(ce2.build(block=seq+st,volst=vs),name)
    except AssertionError as e: r={'name':name,'err':str(e)[:200]}
    return r
if __name__=='__main__':
    n=int(sys.argv[1]); random.seed(7)
    P=list(itertools.permutations(ST)); random.shuffle(P)
    A=[(p,vs,random.randint(0,7)) for p in P[:n] for vs in (True,)]
    with Pool(5) as p:
        for r in p.imap_unordered(job,A,chunksize=4): print(json.dumps(r),flush=True)
