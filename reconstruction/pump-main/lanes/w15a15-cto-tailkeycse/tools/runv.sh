#!/bin/bash
# runv.sh <edits.py> <variant> <slot>: copy the lane crate, apply EDITS V[variant], measure.sh it, print one JSON line.
E=$1; N=$2; W=$3
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a15-cto-tailkeycse
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a15-cto-tailkeycse
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/tools
rm -rf $OUT/var/$N; mkdir -p $OUT/var; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $E $N <<'PY' || exit 1
import sys,runpy
f,p,n=sys.argv[1:4]; s=open(f).read(); V=runpy.run_path(p)['V']; n0=s.count('\n')
for a,b in V[n]:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b,1)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
$TOOLS/measure.sh $OUT/var/$N $OUT/work$W $OUT/t/$N | tail -1 | python3 -c "
import json,sys; d=json.loads(sys.stdin.read()); c=d.get('admin_cto') or {}
print(json.dumps({'v':'$N','ok':d.get('ok'),'ratio':c.get('ratio'),'slots':c.get('slots_diff'),'bytes':c.get('cand_bytes'),'norm':d.get('normalized'),'raw':d.get('raw'),'losses':len(d.get('losses',[])),'raw_losses':len(d.get('raw_losses',[])),'err':str(d.get('error',''))[-300:]}))"
rm -f $OUT/t/$N/*.so.tmp 2>/dev/null
