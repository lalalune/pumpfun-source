#!/bin/bash
# cs.sh <name> <edits.py|-> <slot>: copy worktree crate, apply EDITS=[(old,new)] to admin_cto.rs (line count kept), capture raw IR, rx score, mm
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a05-cto-rw7walletr8
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a05-cto-rw7walletr8
N=$1; E=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
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
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/cap_$N.log 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -rh -m3 -A7 '^error' $OUT/ir/cap_$N* 2>/dev/null | head -30 >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/ir/cap_$N.log $OUT/var/$N
cd $OUT && python3 tools/rx.py $N --base ir/$N.ll | tail -1 && python3 tools/mm.py $N
[ "$KEEPIR" = 1 ] || rm -f ir/$N.ll
