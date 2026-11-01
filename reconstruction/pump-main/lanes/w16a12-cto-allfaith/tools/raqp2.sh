#!/bin/bash
# raqp2.sh name...: pass-2 RA joint (lpipe with the pass-1 forces as base, TAGSFX=p2), then stk.sh with the p2 forces -> data/stkra.jsonl
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a12-cto-allfaith
for n in "$@"; do
  while [ ! -f rx/${n}ra/force.txt ]; do sleep 20; done
  F1=$(sed -n 's/^FORCE //p' rx/${n}ra/force.txt)
  [ -f rx/${n}p2ra/force.txt ] || TAGSFX=p2 t2/lpipe.sh $n 80 30 12 2 "$F1" > cm/$n.lpipe_p2.log 2>&1
  F=$(sed -n 's/^FORCE //p' rx/${n}p2ra/force.txt)
  t2/stk.sh $n "$F" p2 > /dev/null 2>&1
  python3 - $n <<'PY'
import json,sys; n=sys.argv[1]; r=json.load(open(f'stk/{n}_p2/stk.json')); r['n']=n; r['pass']='p2'
open('data/stkra.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps({k:r[k] for k in ('n','pass','nforce','bytes','M_plain','Mfnhc_plain','Mfnhc','stacked')}))
PY
done
