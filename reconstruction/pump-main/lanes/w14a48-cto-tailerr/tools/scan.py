import sys,subprocess,json
from concurrent.futures import ThreadPoolExecutor
base,jobs,out=sys.argv[1],sys.argv[2],sys.argv[3]
J=[l.rstrip('\n').split('\t') for l in open(jobs)]
def run(j):
    k,spec=j[0],j[1:]
    r=subprocess.run(['python3','tools/bmove.py',base,'s'+k,*spec],capture_output=True,text=True)
    try: d=json.loads(r.stdout.strip().split('\n')[-1])
    except Exception: d={'error':r.stderr[-200:]}
    d['spec']=spec; subprocess.run(['rm','-rf','bm/s'+k]); return d
with ThreadPoolExecutor(3) as ex, open(out,'w') as f:
    for d in ex.map(run,J): f.write(json.dumps(d)+'\n'); f.flush()
