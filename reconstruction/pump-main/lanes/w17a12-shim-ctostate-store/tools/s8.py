import sys,os,re,json
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ce2,pscore
BLK=['mf','he','fc','s_cb','s_hr','s_my','cr','s_ql','s_fc','s_he','s_mf']
T0=ce2.build(early=('cb','hr','my'),G=True,block=BLK,volst=True)
fs=T0.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); fe=T0.index('\n}\n',fs)
FN=T0[fs:fe].split('\n')
def job(a):
    k,kind=a
    L=list(FN)
    if kind=='l': L[k]=L[k].replace('= load ','= load volatile ',1)
    else: L[k]=L[k].replace('store ','store volatile ',1)
    name='ve_%s%d'%(kind,k)
    try: r=pscore.score_text(T0[:fs]+'\n'.join(L)+T0[fe:],name)
    except Exception as e: r={'name':name,'err':str(e)[:100]}
    r['line']=FN[k].strip()[:100]; return r
if __name__=='__main__':
    A=[]
    for k,l in enumerate(FN):
        if re.match(r'\s+%\S+ = load (i8|i16|i32|i64|ptr),',l) and 'volatile' not in l: A.append((k,'l'))
        elif re.match(r'\s+store (i8|i16|i32|i64|ptr) ',l) and 'volatile' not in l: A.append((k,'s'))
    print(len(A),file=sys.stderr)
    print(json.dumps(pscore.score_text(T0,'ve_base')),flush=True)
    with Pool(6) as p:
        for r in p.imap_unordered(job,A,chunksize=8): print(json.dumps(r),flush=True)
