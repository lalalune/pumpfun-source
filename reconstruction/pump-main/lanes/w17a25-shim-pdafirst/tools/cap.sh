#!/bin/bash
# cap.sh <name> <edits.py> [work] [base crate]: crate copy + exact edits -> capraw (pre-opt IR) -> preslim -> fx (exact slim oracle). Experiment only.
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a25-shim-pdafirst
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a25-shim-pdafirst
n=$1; e=$2; w=${3:-work1}; B=${4:-$WT/programs/pump}
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n $OUT/ir/$n
rsync -a --exclude target $B/ $OUT/var/$n/
python3 $OUT/tools/apply.py $OUT/var/$n/src/creator/admin_cto.rs $e || { echo "{\"name\":\"$n\",\"err\":\"apply\"}"; exit 1; }
find $OUT/$w -name "pump_recovered*.ll" -delete 2>/dev/null
PUMP_BUILD_SLOTS=10 python3 $OUT/t6/capraw.py $OUT/var/$n $OUT/$w $OUT/ir/$n > $OUT/ir/$n.cap.log 2>&1 || true
if grep -q "^error\[E" $OUT/ir/$n.cap.log; then echo "{\"name\":\"$n\",\"err\":\"rustc\"}"; grep -A3 "^error\[E" $OUT/ir/$n.cap.log | head -8; rm -rf $OUT/var/$n $OUT/ir/$n $OUT/fx/$n; exit 1; fi
if [ ! -s $OUT/ir/$n/raw.ll ]; then echo "{\"name\":\"$n\",\"err\":\"capraw\"}"; tail -5 $OUT/ir/$n.cap.log; rm -rf $OUT/var/$n; exit 1; fi
SURV=$OUT/t6/surv-1647da0.txt python3 $OUT/t6/preslim.py $OUT/ir/$n/raw.ll $OUT/ir/$n.slim.ll keep > /dev/null
rm -rf $OUT/ir/$n $OUT/var/$n
LANE_OUT=$OUT python3 $OUT/t6/fx.py $OUT/ir/$n.slim.ll $n --keep
