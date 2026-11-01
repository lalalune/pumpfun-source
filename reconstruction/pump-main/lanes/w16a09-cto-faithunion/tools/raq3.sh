#!/bin/bash
# pass N (>=3): colmap/screen/climb on top of the previous pass's forces, then the stacked bound. raq3.sh <rx> <prevtag> <tag>
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a09-cto-faithunion
n=$1; pt=$2; t=$3
B=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/${n}${pt}.climb.log') if l.startswith('{')]; print(L[-1]['force'])")
if [ ! -f cm/${n}${t}.climb.log ] || ! grep -q '^{' cm/${n}${t}.climb.log; then t2/pass2.sh $n $t "$B" > cm/$n.$t.log 2>&1; fi
F=$(python3 -c "
import json
L=[json.loads(l) for l in open('cm/${n}${t}.climb.log') if l.startswith('{')]; print(L[-1]['force'] if L and L[-1].get('force') else '$B')")
t2/stk.sh $n "$F" $t > /dev/null 2>&1
python3 - $n $t <<'PY'
import json,sys; n,t=sys.argv[1:3]; r=json.load(open(f'stk/{n}_{t}/stk.json')); r['n']=n; r['pass']=t
open('data/stkra.jsonl','a').write(json.dumps(r)+'\n'); print(json.dumps({k:r[k] for k in ('n','pass','nforce','bytes','M_plain','Mfnhc_plain','Mfnhc','stacked')}))
PY
