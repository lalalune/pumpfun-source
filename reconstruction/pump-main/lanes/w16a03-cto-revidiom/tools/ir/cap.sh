#!/bin/bash
# cap.sh <name> <edits.py|-> <slot>: crate copy + edits to admin_cto.rs (line count kept), capture raw IR to ir/<name>.ll, then rx --keep
OUT=~/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a03-cto-revidiom
N=$1; E=$2; W=$3
rm -rf $OUT/var/$N; mkdir -p $OUT/var; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
if [ "$E" != "-" ]; then python3 - $OUT/var/$N/src/creator/admin_cto.rs "$E" <<'PY' || exit 1
import sys,runpy
f,e=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for a,b in runpy.run_path(e)['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
fi
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/work$W
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/ir/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/cap_$N.log 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -h -m3 -A8 "^error" $OUT/ir/cap_$N.log $OUT/ir/cap_$N/*.log 2>/dev/null | head -30 >&2; rm -rf $OUT/ir/cap_$N $OUT/var/$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll && rm -rf $OUT/ir/cap_$N $OUT/var/$N
cd $OUT && python3 tools/ir/rx.py $N --base ir/$N.ll --keep | tail -1
