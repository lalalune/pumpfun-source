#!/bin/bash
# cap.sh <name> <admin_cto.rs> <work>: crate copy with given admin_cto.rs, capture build, trim to ir/<name>/mod.ll, score
set -u
N=$1; B=$2; W=$3
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a47-cto-stitch9; WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a47-cto-stitch9; S=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a47-cto-stitch9/reconstruction/pump-main/lanes/w13a47-cto-stitch9/scripts
rm -rf $O/var/$N; mkdir -p $O/var; rsync -a --exclude target $WT/programs/pump/ $O/var/$N/
cp $B $O/var/$N/src/creator/admin_cto.rs
mkdir -p $O/ir/$N
PUMP_BUILD_SLOTS=10 python3 $S/capture.py $O/var/$N $O/$W $O/ir/$N > $O/ir/$N.build.json 2>&1
[ -f $O/ir/$N/unstripped.so ] || { echo "$N build failed"; tail -c 600 $O/ir/$N.build.json; exit 1; }
echo "$N $(python3 $S/ctoracle.py so $O/ir/$N/unstripped.so)"
python3 $S/getfn.py $O/ir/$N/pump_recovered.ll $O/ir/$N && rm -f $O/ir/$N/pump_recovered.ll $O/ir/$N/candidate.so $O/ir/$N/link.map $O/ir/$N/unstripped.so
rm -rf $O/var/$N
