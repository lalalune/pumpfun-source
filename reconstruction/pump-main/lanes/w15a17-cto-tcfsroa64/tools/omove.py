# omove.py <mn.ll> <defline1> <lastline1> : move the 2-line unit at defline1 (1-based) to before every later
# non-phi instruction up to lastline1; score each with px2 (IR oracle only)
import sys,os,json,re
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,os.path.dirname(__file__)); import px2
f,d,e=sys.argv[1],int(sys.argv[2])-1,int(sys.argv[3])-1
L=open(f).read().split('\n'); U=L[d:d+2]; R=L[:d]+L[d+2:]
pos=[i for i in range(d,e-2) if R[i].startswith('  ') and ' phi ' not in R[i]]
os.makedirs('perm',exist_ok=True)
def run(i):
    t=R[:i]+U+R[i:]; fn=f'perm/om{i}.ll'; open(fn,'w').write('\n'.join(t)); r=px2.run(fn); os.remove(fn)
    return {'i':i+1,'before':R[i].strip()[:70],**{k:r.get(k) for k in ('ratio','M','bytes','slots')}}
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(run,pos): print(json.dumps(r),flush=True)
