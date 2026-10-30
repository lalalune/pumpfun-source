#!/bin/bash
# cap.sh <name> <base.rs> <work> [genes...]: crate copy + genes, capture build with post-opt IR, trim to mod.ll, score
set -u
N=$1; B=$2; W=$3; shift 3
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a30-cto-stitch8; WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a30-cto-stitch8; S=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a30-cto-stitch8/reconstruction/pump-main/lanes/w13a30-cto-stitch8/scripts
rm -rf $O/var/$N; rsync -a --exclude target $WT/programs/pump/ $O/var/$N/
python3 -c "
import sys; sys.path.insert(0,'$O/tools'); import genes30 as g
s=open('$B').read(); open('$O/var/$N/src/creator/admin_cto.rs','w').write(g.apply(sys.argv[1:],s))" "$@" || exit 1
mkdir -p $O/ir/$N
PUMP_BUILD_SLOTS=10 python3 $S/capture.py $O/var/$N $O/$W $O/ir/$N > $O/ir/$N.build.json 2>&1
[ -f $O/ir/$N/unstripped.so ] || { echo "$N build failed"; tail -c 600 $O/ir/$N.build.json; exit 1; }
echo "$N $(python3 $S/ctoracle.py so $O/ir/$N/unstripped.so)"
python3 $S/getfn.py $O/ir/$N/pump_recovered.ll $O/ir/$N && rm -f $O/ir/$N/pump_recovered.ll $O/ir/$N/candidate.so $O/ir/$N/link.map $O/ir/$N/unstripped.so
rm -rf $O/var/$N
