#!/bin/bash
# cap.sh <name> <edits.py> [work]: crate copy + exact edits -> capraw (pre-opt IR) -> preslim -> fx (exact slim oracle). Experiment only.
set -e
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a08-shim-sscorder
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a08-shim-sscorder
TL=$WT/reconstruction/pump-main/lanes/w17a08-shim-sscorder/tools
n=$1; e=$2; w=${3:-work1}
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n $OUT/ir/$n
rsync -a --exclude target $WT/programs/pump/ $OUT/var/$n/
python3 $TL/apply.py $OUT/var/$n/src/creator/admin_cto.rs $e
PUMP_BUILD_SLOTS=10 python3 $OUT/t6/capraw.py $OUT/var/$n $OUT/$w $OUT/ir/$n > $OUT/ir/$n.cap.log 2>&1 || true
SURV=$OUT/t6/surv-1647da0.txt python3 $OUT/t6/preslim.py $OUT/ir/$n/raw.ll $OUT/ir/$n.slim.ll keep > /dev/null
rm -f $OUT/ir/$n/raw.ll
LANE_OUT=$OUT python3 $OUT/t6/fx.py $OUT/ir/$n.slim.ll $n --keep
