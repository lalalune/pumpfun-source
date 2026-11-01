#!/bin/bash
# run.sh <name> <genes> <slot> [base]: make variant, measure, append summary to res/R.txt, keep json
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a02-shim-unlockplace
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a02-shim-unlockplace
N=$1; G=$2; W=$3; B=${4:-$WT/programs/pump}
python3 $OUT/tools/mk.py $B $OUT/var/$N "$G" > /dev/null || { echo "$N $G GENEFAIL" >> $OUT/res/R.txt; exit 1; }
r=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>&1 | tail -1)
echo "$r" > $OUT/res/$N.json
python3 - "$N" "$G" "$r" >> $OUT/res/R.txt <<'PY'
import json,sys
n,g,r=sys.argv[1:4]
try: d=json.loads(r)
except Exception: print(n,g,'BADJSON',r[:300]); sys.exit()
if not d.get('ok'): print(n,g,'FAIL',str(d.get('error'))[-400:].replace('\n',' ')); sys.exit()
c=d['admin_cto']; print(n,g,'norm',d['normalized'],'raw',d['raw'],'L',len(d['losses']),len(d['raw_losses']),'ratio',c['ratio'],'slots',c['slots_diff'],'bytes',c['cand_bytes'],'calls',c['calls_candidate'],'sha',d['sha'])
PY
rm -rf $OUT/var/$N
tail -1 $OUT/res/R.txt
