import sys,os,re,json
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ce2,pscore
BLK=['mf','he','fc','s_cb','s_hr','s_my','cr','s_ql','s_fc','s_he','s_mf']
MODE=os.environ.get('S9BASE','ve')
T0=ce2.build(early=('cb','hr','my'),G=True,block=BLK,volst=True) if MODE=='ve' else ce2.BASE
fs=T0.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); fe=T0.index('\n}\n',fs)
FN=T0[fs:fe].split('\n')
# find a free metadata id
mx=max(int(x) for x in re.findall(r'^!(\d+) = ',T0,re.M))
MD={'hi':mx+1,'lo':mx+2}
EXTRA='\n!%d = !{!"branch_weights", i32 2000, i32 1}\n!%d = !{!"branch_weights", i32 1, i32 2000}\n'%(MD['hi'],MD['lo'])
def job(a):
    k,w=a
    L=list(FN)
    if '!prof' in L[k]: return {'name':'skip'}
    L[k]=L[k]+', !prof !%d'%MD[w]
    name='%s_bw%s%d'%(MODE,w,k)
    try: r=pscore.score_text(T0[:fs]+'\n'.join(L)+T0[fe:]+EXTRA,name)
    except Exception as e: r={'name':name,'err':str(e)[:100]}
    r['line']=FN[k].strip()[:100]; return r
if __name__=='__main__':
    A=[(k,w) for k,l in enumerate(FN) if re.match(r'\s+br i1 ',l) for w in ('hi','lo')]
    print(len(A),file=sys.stderr)
    with Pool(6) as p:
        for r in p.imap_unordered(job,A,chunksize=8): print(json.dumps(r),flush=True)
