#!/bin/bash
# capvar.sh <name> <varsfile.py> [work]: crate copy + V[name] edits (line count kept) -> raw IR -> slim -> fx score; prints json
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a29-shim-feetagpt
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a29-shim-feetagpt
n=$1; vf=$2; w=${3:-work1}
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n
rsync -a --exclude target $WT/programs/pump/ $OUT/var/$n/
python3 - "$OUT/var/$n/src/creator/admin_cto.rs" "$vf" "$n" <<'PY' || exit 1
import sys,runpy
f,vf,n=sys.argv[1:4]; V=runpy.run_path(vf)['V']; t=open(f).read(); n0=t.count('\n')
for a,b in V[n]:
    c=t.count(a); assert c==1,(n,c,a[:100]); t=t.replace(a,b)
assert t.count('\n')==n0,'line count changed'
open(f,'w').write(t)
PY
rm -f $OUT/$w/target*/*/release/deps/pump_recovered*.ll
rm -rf $OUT/ir/cap_$n
for attempt in 1 2 3; do
  PUMP_BUILD_SLOTS=10 python3 $OUT/tools/capraw.py $OUT/var/$n $OUT/$w $OUT/ir/cap_$n > $OUT/ir/$n.cap.log 2>&1
  [ -f $OUT/ir/cap_$n/raw.ll ] && break
  grep -qE "ENFILE|Too many open files|temporarily unavailable|cannot lock ref" $OUT/ir/$n.cap.log || break
  sleep 20
done
if [ ! -f $OUT/ir/cap_$n/raw.ll ]; then echo "{\"name\":\"$n\",\"err\":\"capture failed\"}"; grep -m3 "^error" $OUT/ir/$n.cap.log; exit 1; fi
mv $OUT/ir/cap_$n/raw.ll $OUT/ir/$n.raw.ll && rm -rf $OUT/ir/cap_$n $OUT/var/$n
SURV=$OUT/tools/surv-1647da0.txt python3 $OUT/tools/preslim.py $OUT/ir/$n.raw.ll $OUT/ir/$n.slim.ll keep > /dev/null && rm -f $OUT/ir/$n.raw.ll
LANE_OUT=$OUT python3 $OUT/tools/fx.py $OUT/ir/$n.slim.ll $n --keep
