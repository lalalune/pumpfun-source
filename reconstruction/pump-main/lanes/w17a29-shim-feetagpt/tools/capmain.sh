#!/bin/bash
# capture main's pre-opt IR and slim it
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a29-shim-feetagpt
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a29-shim-feetagpt
n=$1; src=${2:-$WT/programs/pump}; w=${3:-work0}
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n
rsync -a --exclude target $src/ $OUT/var/$n/
rm -f $OUT/$w/target*/*/release/deps/pump_recovered*.ll
rm -rf $OUT/ir/cap_$n
PUMP_BUILD_SLOTS=10 python3 $OUT/tools/capraw.py $OUT/var/$n $OUT/$w $OUT/ir/cap_$n > $OUT/ir/$n.cap.log 2>&1
mv $OUT/ir/cap_$n/raw.ll $OUT/ir/$n.raw.ll && rm -rf $OUT/ir/cap_$n $OUT/var/$n
SURV=$OUT/tools/surv-1647da0.txt python3 $OUT/tools/preslim.py $OUT/ir/$n.raw.ll $OUT/ir/$n.slim.ll keep > /dev/null
LANE_OUT=$OUT python3 $OUT/tools/fx.py $OUT/ir/$n.slim.ll $n --keep
