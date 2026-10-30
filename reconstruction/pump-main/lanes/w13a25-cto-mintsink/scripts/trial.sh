#!/bin/bash
# trial.sh <name> <genes> [work]: crate copy + genes, capture build (IR kept as trimmed mod.ll), cto metric + clonefeat
set -u
D=$(cd "$(dirname "$0")" && pwd); WT=$(cd "$D/../../../../.." && pwd)
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w13a25-cto-mintsink; N=$1; G=$2; W=${3:-work0}
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 $D/var.py $OUT/var/$N $G || exit 1
mkdir -p $OUT/ir/$N
python3 $D/capture.py $OUT/var/$N $OUT/$W $OUT/ir/$N > $OUT/ir/$N.build.json 2>&1
[ -f $OUT/ir/$N/unstripped.so ] || { echo "$N build failed"; grep -m3 -A5 '^error' $OUT/ir/$N/build.log $OUT/ir/$N.build.json | head -20; exit 1; }
echo "$N $G $(python3 $D/ctoracle.py so $OUT/ir/$N/unstripped.so) cf=$(python3 $D/clonefeat.py $OUT/ir/$N/unstripped.so | tail -1 | sed 's/.*spill/spill/')"
python3 $D/getfn.py $OUT/ir/$N/pump_recovered.ll $OUT/ir/$N && rm -f $OUT/ir/$N/pump_recovered.ll $OUT/ir/$N/candidate.so $OUT/ir/$N/link.map
rm -rf $OUT/var/$N
