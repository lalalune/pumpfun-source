#!/bin/bash
# run.sh <name> <spec-json> <slot>
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a37-cto-skelregress
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a37-cto-skelregress
N=$1; SPEC=$2; W=$3
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 $OUT/tools/var.py $OUT/var/$N/src/creator/admin_cto.rs "$SPEC" || { echo "{\"name\":\"$N\",\"error\":\"spec\"}" >> $OUT/results.jsonl; exit 1; }
R=$(/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N 2>&1 | tail -1)
SK=""
if [ -f $OUT/t/$N/unstripped.so ]; then SK=$(cd $OUT/tools && python3 reg.py $OUT/t/$N/unstripped.so 2>/dev/null | grep skel); fi
python3 - "$N" "$SPEC" "$R" "$SK" >> $OUT/results.jsonl <<'PY'
import json,sys
n,spec,r,sk=sys.argv[1:5]
try: d=json.loads(r)
except Exception: d={'ok':False,'err':r[-300:]}
o={'name':n,'ok':d.get('ok'),'cto':d.get('admin_cto'),'losses':d.get('losses'),'raw_losses':d.get('raw_losses'),'gains':d.get('gains'),'sha':d.get('sha'),'skel':sk,'spec':spec}
if not d.get('ok'): o['err']=str(d.get('error',d.get('err','')))[-400:]
print(json.dumps(o))
PY
rm -rf $OUT/var/$N
