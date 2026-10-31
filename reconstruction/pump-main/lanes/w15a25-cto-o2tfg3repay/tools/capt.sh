#!/bin/bash
# capt.sh <name> <genes> <slot>: copy main crate, apply genes, capture raw IR (one build), then the fast V oracle
# (reduce.py + thr.py + vbfi.py, seconds) -> trig2.txt. Keeps ir/<name>.ll for a later rx run.
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a25-cto-o2tfg3repay
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}; R=${RES:-$OUT/trig2.txt}
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || { echo "$N $G | GENE FAIL" >> $R; exit 1; }
import sys
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay/s12')
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay/tools')
import genes, mine, og, tg, g25
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for name in g.split('+'):
    eds=g25.G[name] if name in g25.G else tg.G[name] if name in tg.G else og.G[name] if name in og.G else (mine.G.get(name) or genes.G[name])
    for a,b in eds:
        c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "$N $G | COMPILE FAIL $(grep -h -m1 -A3 '^error' $OUT/ir/cap_$N/*.log 2>/dev/null | tr '\n' ' ' | cut -c1-300)" >> $R; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT; python3 tools/reduce.py ir/$N.ll ir/red_$N.ll 2>/dev/null
echo "$N $G | V $(python3 tools/vbfi.py ir/red_$N.ll) | THR $(python3 tools/thr.py ir/red_$N.ll)" >> $R
