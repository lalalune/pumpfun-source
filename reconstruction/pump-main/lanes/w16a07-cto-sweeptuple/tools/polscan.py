#!/usr/bin/env python3
"""polscan.py <m.ll> <out.jsonl> [lo hi]: post-opt IR polarity oracle (experiment only). For each `br i1` block B (IR index
in [lo,hi)) whose IR-next block is neither successor, move each successor S (and, separately, S plus nothing else) to
right after B and score with irmv.py. A successor made IR-next flips ISel's branch polarity at B (jeq+ja <-> jne)."""
import sys,os,re,subprocess,json
from concurrent.futures import ThreadPoolExecutor
T=os.path.dirname(os.path.abspath(__file__))
src,outf=sys.argv[1],sys.argv[2]; lo=int(sys.argv[3]) if len(sys.argv)>3 else 0; hi=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
t=open(src).read(); i=t.index('define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute'); j=t.index('\n}\n',i)
parts=re.split(r'\n(?=[\w.$"-]+:)',t[i:j])[1:]
nm=lambda b:b.split('\n',1)[0].split(':')[0].strip('"')
names=[nm(b) for b in parts]
jobs=[]
for k,b in enumerate(parts):
    if not(lo<=k<hi): continue
    m=re.search(r'\n\s*br i1 [^,]+, label %("[^"]+"|[\w.$-]+), label %("[^"]+"|[\w.$-]+)\s*$',b)
    if not m: continue
    s1,s2=m.group(1).strip('"'),m.group(2).strip('"'); nxt=names[k+1] if k+1<len(names) else None
    if nxt in (s1,s2): continue
    for s in (s1,s2):
        if s==names[k]: continue
        jobs.append((k,names[k],s))
done=set()
if os.path.exists(outf):
    for l in open(outf): d=json.loads(l); done.add((d['b'],d['s']))
def run(job):
    k,b,s=job
    if (b,s) in done: return None
    nmx=f'ps_{k}_{abs(hash(s))%100000}'
    r=subprocess.run(['python3',T+'/irmv.py',src,nmx,f'{s}@{b}'],capture_output=True,text=True)
    try: d=json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: d={'error':(r.stdout+r.stderr)[-200:]}
    d.update({'k':k,'b':b,'s':s}); 
    import shutil; shutil.rmtree(os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a07-cto-sweeptuple/rx/'+nmx),ignore_errors=True)
    with open(outf,'a') as f: f.write(json.dumps(d)+'\n')
    return d
print(len(jobs),'jobs',flush=True)
with ThreadPoolExecutor(int(os.environ.get('NP','3'))) as ex:
    for d in ex.map(run,jobs):
        if d and d.get('M',0)>=2245: print(json.dumps(d),flush=True)
