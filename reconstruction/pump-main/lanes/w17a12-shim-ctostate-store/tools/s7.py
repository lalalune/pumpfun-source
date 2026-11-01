import sys,os,re,json
from multiprocessing import Pool
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ce2,pscore
T0=ce2.BASE
fs=T0.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); fe=T0.index('\n}\n',fs)
FN=T0[fs:fe].split('\n')
CB='  %i33 = load i8, ptr %i32, align 1, !range !15, !noundef !2'
HE='  %i35 = load i8, ptr %i34, align 1, !range !15, !noundef !2'
def apply(base_pins,k,kind):
    L=list(FN)
    for bp in base_pins:
        idx=L.index(bp); L[idx]=L[idx].replace('= load ','= load volatile ',1)
    if k is not None:
        if kind=='l': L[k]=L[k].replace('= load ','= load volatile ',1)
        else: L[k]=L[k].replace('store ','store volatile ',1)
    return T0[:fs]+'\n'.join(L)+T0[fe:]
def job(a):
    base,k,kind=a
    name='%s_%s%d'%('+'.join('cb' if b==CB else 'he' for b in base),kind,k)
    try: r=pscore.score_text(apply(base,k,kind),name)
    except Exception as e: r={'name':name,'err':str(e)[:100]}
    r['k']=k; r['kind']=kind; r['line']=FN[k].strip()[:100]
    return r
if __name__=='__main__':
    cand=[]
    for k,l in enumerate(FN):
        if re.match(r'\s+%\S+ = load (i8|i16|i32|i64|ptr),',l) and 'volatile' not in l and l not in (CB,HE): cand.append((k,'l'))
        elif re.match(r'\s+store (i8|i16|i32|i64|ptr) ',l) and 'volatile' not in l: cand.append((k,'s'))
    bases=[[CB],[HE]]
    A=[(b,k,kind) for b in bases for k,kind in cand]
    print(len(A),file=sys.stderr)
    with Pool(6) as p:
        for r in p.imap_unordered(job,A,chunksize=8): print(json.dumps(r),flush=True)
