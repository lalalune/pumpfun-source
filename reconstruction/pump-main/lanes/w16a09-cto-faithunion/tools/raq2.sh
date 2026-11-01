#!/bin/bash
# pass 2: colmap/screen/climb on top of the pass-1 forces, then the stacked bound with the pass-2 force set
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion
for n in "$@"; do
  while [ ! -f rx/${n}ra/force.txt ]; do sleep 20; done
  B=$(sed -n 's/^FORCE //p' rx/${n}ra/force.txt)
  if [ ! -f cm/${n}p2.climb.log ] || ! grep -q '^{' cm/${n}p2.climb.log; then t2/pass2.sh $n p2 "$B" > cm/$n.p2.log 2>&1; fi
  F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/${n}p2.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '$B')")
  t2/stk.sh $n "$F" p2 > /dev/null 2>&1
  python3 - $n <<'PY'
import json,sys; n=sys.argv[1]; r=json.load(open(f'stk/{n}_p2/stk.json')); r['n']=n; r['pass']='p2'
open('data/stkra.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps({k:r[k] for k in ('n','nforce','bytes','M_plain','Mfnhc_plain','Mfnhc','stacked')}))
PY
done
