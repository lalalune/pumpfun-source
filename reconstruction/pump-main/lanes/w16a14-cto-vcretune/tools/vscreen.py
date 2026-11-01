#!/usr/bin/env python3
"""vscreen.py <m.ll> <jobs.jsonl> <out.jsonl> [nthreads]: w16a04 t84/screen.py run() in a thread pool (robust to a worker
dying), skipping jobs already in out. Experiment only."""
import sys,os,json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil/t84'); import screen
m,jf,of=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 2
screen.init(m)
done=set()
if os.path.exists(of): done={json.loads(l)['name'] for l in open(of) if l.strip()}
jobs=[json.loads(l) for l in open(jf) if l.strip()]; jobs=[j for j in jobs if j['name'] not in done]
with ThreadPoolExecutor(n) as ex, open(of,'a') as f:
    for res in ex.map(screen.run,jobs):
        f.write(json.dumps(res)+'\n'); f.flush()
