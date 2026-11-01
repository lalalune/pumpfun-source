#!/bin/bash
# mv.sh <name> <edits.py> <slot>: copy worktree crate, apply EDITS (line count kept), measure.sh -> t/<name>, append summary to res.txt
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a03-shim-unlockspill
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a03-shim-unlockspill
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; mkdir -p $OUT/var $OUT/t; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || { echo "{\"name\":\"$N\",\"error\":\"edit\"}" >> $OUT/res.txt; exit 1; }
import sys,runpy
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for a,b in runpy.run_path(g)['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
if [ -f $OUT/var/$N/LIBEDIT ]; then :; fi
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/work$W
R=$($TOOLS/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>/dev/null | tail -1)
echo "$R" > $OUT/t/$N/m.json
python3 - "$N" "$R" >> $OUT/res.txt <<'PY'
import json,sys
n,r=sys.argv[1],sys.argv[2]
try: d=json.loads(r)
except Exception: print(json.dumps({'name':n,'error':'measure','raw':r[:300]})); sys.exit()
if not d.get('ok'): print(json.dumps({'name':n,'error':'build','raw':str(d.get('error'))[-600:]})); sys.exit()
c=d['admin_cto']
print(json.dumps({'name':n,'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'calls':c.get('calls_candidate'),'norm':d['normalized'],'raw':d['raw'],'losses':d['losses'],'raw_losses':len(d['raw_losses']),'gains':d['gains']}))
PY
rm -rf $OUT/var/$N
: keep candidate.so
tail -1 $OUT/res.txt
