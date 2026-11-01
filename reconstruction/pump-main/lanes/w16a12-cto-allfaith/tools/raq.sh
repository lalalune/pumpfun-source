#!/bin/bash
# raq.sh name...: sequential RA joint queue: lpipe pass 1 (P=2) for each name, then stk.sh with the pass-1 forces -> data/stkra.jsonl
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for n in "$@"; do
  while [ ! -f rx/$n/res.json ]; do sleep 20; done
  if [ ! -f rx/${n}ra/force.txt ]; then t2/lpipe.sh $n 80 30 12 2 > cm/$n.lpipe.log 2>&1; fi
  F=$(sed -n 's/^FORCE //p' rx/${n}ra/force.txt)
  t2/stk.sh $n "$F" p1 > /dev/null 2>&1
  python3 - $n <<'PY'
import json,sys; n=sys.argv[1]; r=json.load(open(f'stk/{n}_p1/stk.json')); r['n']=n; r['pass']='p1'
open('data/stkra.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps({k:r[k] for k in ('n','nforce','bytes','M_plain','Mfnhc_plain','Mfnhc','stacked')}))
PY
done
