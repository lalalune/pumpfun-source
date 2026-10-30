#!/bin/bash
# trial.sh <name> <edits.py> <slot 0|1> : copy main crate, apply EDITS to admin_cto.rs (line count kept), measure.sh, print one JSON line
set -u
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a01-cto-irexact
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a01-cto-irexact
N=$1; P=$2; W=$3
mkdir -p $OUT/var $OUT/t
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $P <<'PY' || { echo "{\"name\":\"$N\",\"error\":\"EDIT_FAILED\"}"; exit 1; }
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
for a,b in g['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'newline count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
R=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>&1 | tail -1)
echo "$R" | python3 -c "
import json,sys
try: d=json.loads(sys.stdin.read())
except Exception as e: print(json.dumps({'name':'$N','error':'parse'})); sys.exit()
c=d.get('admin_cto',{}); print(json.dumps({'name':'$N','ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'norm':d.get('normalized'),'raw':d.get('raw'),'losses':d.get('losses'),'raw_losses':len(d.get('raw_losses') or []),'sha':d.get('sha'),'err':d.get('error','')[-300:] if not d.get('ok') else ''}))
" | tee -a $OUT/results.jsonl
rm -f $OUT/t/$N/candidate.so $OUT/t/$N/link.map
