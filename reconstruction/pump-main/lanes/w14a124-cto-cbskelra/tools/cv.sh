#!/bin/bash
# cv.sh <name> <genes(+ joined)|edits.py> <slot>: copy main crate, apply genes (s12/genes.py + mine.py), capture raw IR, rx score
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a124-cto-cbskelra
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a124-cto-cbskelra
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || exit 1
import sys,os
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a124-cto-cbskelra/s12')
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a124-cto-cbskelra/tools')
import genes, mine, my
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for name in [x for x in g.split('+') if x!='none']:
    eds=my.G.get(name) or mine.G.get(name) or genes.G[name]
    for a,b in eds:
        c=s.count(a); assert c==1,(name,c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; tail -5 $OUT/ir/caplog_$N.txt >&2; grep -h -m2 -A6 "^error" $OUT/ir/cap_$N/*.log >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT && python3 tools/rx.py $N --base ir/$N.ll | tail -1
