#!/bin/bash
# capg.sh <name> <gene,gene,...> <slot>: copy worktree crate, apply genes (tools/genes_fp.py, line count kept), capture raw IR
# (identity build, pre-opt IR) -> ir/<name>.ll, then rx (opt -O3 + slim + llc + score) -> rx/<name>
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a24-cto-s3feephi
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a24-cto-s3feephi
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; mkdir -p $OUT/var; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || exit 1
import sys
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a24-cto-s3feephi/tools')
import genes_fb as g
f,names=sys.argv[1],[x for x in sys.argv[2].split(',') if x]
s=open(f).read(); n0=s.count('\n'); t=g.apply(s,names)
assert t.count('\n')==n0,'line count changed'
open(f,'w').write(t)
PY
cp $OUT/var/$N/src/creator/admin_cto.rs $OUT/src/$N.rs
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/work$W
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/t2/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -m5 "^error" $OUT/ir/caplog_$N.txt; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT && nice -n 5 python3 t2/rx.py $N --base ir/$N.ll
