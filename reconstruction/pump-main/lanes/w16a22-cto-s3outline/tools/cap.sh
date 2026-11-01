#!/bin/bash
# cap.sh <name> <genes joined by +> <slot> [norx]: copy the worktree crate, apply s3g genes in order (line count kept),
# capture raw IR (one identity build), V oracle (reduce+vbfi+thr) -> res/V.txt, then rx (opt -O3 + SDK llc) -> rx/<name>.
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a22-cto-s3outline
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a22-cto-s3outline
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}; R=$OUT/res/V.txt; mkdir -p $OUT/var $OUT/ir $OUT/res
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || { echo "$N $G | GENE FAIL" >> $R; exit 1; }
import sys
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a22-cto-s3outline/tools')
import s3g
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for name in [x for x in g.split('+') if x]:
    for e in s3g.G[name]:
        if callable(e): s=e(s); continue
        a,b=e; c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
cp $OUT/var/$N/src/creator/admin_cto.rs $OUT/res/src_$N.rs
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/work$W
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "$N $G | COMPILE FAIL $(grep -h -m1 -A6 '^error' $OUT/ir/cap_$N/*.log $OUT/ir/caplog_$N.txt 2>/dev/null | tr '\n' ' ' | cut -c1-400)" >> $R; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT; python3 tools/reduce.py ir/$N.ll ir/red_$N.ll 2>/dev/null
echo "$N $G | V $(python3 tools/vbfi.py ir/red_$N.ll 2>&1 | tail -1) | THR $(python3 tools/thr.py ir/red_$N.ll 2>&1 | tail -1)" >> $R
rm -f ir/red_$N.ll
if [ "$4" != "norx" ]; then python3 t2/rx.py $N --base ir/$N.ll > res/rx_$N.txt 2>&1; echo "$N RX $(tail -1 res/rx_$N.txt)" >> $R; fi
echo "done $N $(date +%T)"
