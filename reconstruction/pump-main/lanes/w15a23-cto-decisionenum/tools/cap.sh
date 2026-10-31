#!/bin/bash
# cap.sh <name> <edits.py|-> <slot>: crate copy + edits, capture raw IR to ir/<name>.ll, then rx --keep
OUT=~/.cache/pumpfun-reconstruction/lanes/w15a23-cto-decisionenum
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a23-cto-decisionenum
N=$1; E=$2; W=$3
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
if [ "$E" != "-" ]; then python3 - $OUT/var/$N/src/creator/admin_cto.rs "$E" <<'PY' || exit 1
import sys,runpy
f,e=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for a,b in runpy.run_path(e)['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
fi
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/t118/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/cap_$N.log 2>&1
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll && rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT && python3 t118/rx.py $N --base ir/$N.ll --keep | tail -1; touch $OUT/cap_$N.done
