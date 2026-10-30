#!/bin/bash
# trial.sh <name> <genes> [work]: crate copy of the worktree + genes, capture build (IR kept), cto metric + clonefeat
set -u
D=$(cd "$(dirname "$0")" && pwd); WT=$(cd "$D/../../../../.." && pwd)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w13a21-cto-clonefeat; N=$1; G=$2; W=${3:-work0}
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 $D/var.py $OUT/var/$N $G || exit 1
python3 $D/capture.py $OUT/var/$N $OUT/$W $OUT/ir/$N > $OUT/ir/$N.build.json 2>&1
[ -f $OUT/ir/$N/unstripped.so ] || { echo "$N build failed"; tail -c 600 $OUT/ir/$N.build.json; exit 1; }
echo "$N $(python3 $D/ctoracle.py so $OUT/ir/$N/unstripped.so) cf=$(python3 $D/clonefeat.py $OUT/ir/$N/unstripped.so | tail -1 | sed 's/.*spill/spill/')"
python3 $D/getfn.py $OUT/ir/$N/pump_recovered.ll $OUT/ir/$N && rm -f $OUT/ir/$N/pump_recovered.ll $OUT/ir/$N/candidate.so $OUT/ir/$N/link.map
rm -rf $OUT/var/$N
