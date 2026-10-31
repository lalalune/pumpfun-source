#!/bin/bash
# capvar.sh <name> <edits.py> <slot>: copy main crate, apply source EDITS, capture raw IR to ir/<name>.ll, run rx oracle
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a69-cto-sweptr9
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a69-cto-sweptr9
N=$1; P=$2; W=$3
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $P <<'PY' || exit 1
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
for a,b in g["EDITS"]:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > /dev/null 2>&1
if grep -q '^error' $OUT/ir/cap_$N/build.log || [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -m2 -A3 '^error' $OUT/ir/cap_$N/build.log >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll
rm -rf $OUT/ir/cap_$N
cd $OUT && python3 tools/rx.py $N --base ir/$N.ll $RXARGS | tail -1
