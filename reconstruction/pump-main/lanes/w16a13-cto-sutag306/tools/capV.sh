#!/bin/bash
# capV.sh <name> <genes(+ joined)> <slot> [rx]: copy worktree crate, apply sg genes, capture raw IR (one identity build),
# then the fast V oracle (reduce+vbfi+thr) -> res/V.txt; with 4th arg "rx" also opt -O3 + llc (rx.py) -> rx/<name>.
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a13-cto-sutag306
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a13-cto-sutag306
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}; R=$OUT/res/V.txt; mkdir -p $OUT/var $OUT/ir $OUT/res
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || { echo "$N $G | GENE FAIL" >> $R; exit 1; }
import sys
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a13-cto-sutag306/tools')
import sg
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for name in [x for x in g.split('+') if x]:
    for e in sg.G[name]:
        if callable(e): s=e(s); continue
        a,b=e; c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "$N $G | COMPILE FAIL $(grep -h -m1 -A6 '^error' $OUT/ir/cap_$N/*.log $OUT/ir/caplog_$N.txt 2>/dev/null | tr '\n' ' ' | cut -c1-400)" >> $R; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT; python3 tools/reduce.py ir/$N.ll ir/red_$N.ll 2>/dev/null
echo "$N $G | V $(python3 tools/vbfi.py ir/red_$N.ll) | THR $(python3 tools/thr.py ir/red_$N.ll)" >> $R
if [ "$4" = "rx" ]; then python3 tools/rx.py $N --base ir/$N.ll > res/rx_$N.txt 2>&1; echo "$N RX $(tail -1 res/rx_$N.txt)" >> $R; fi
