#!/bin/bash
# cv2.sh <name> <edits.py> <slot>: copy worktree crate, apply EDITS to admin_cto.rs (line count must hold), capture raw IR, rx score
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a27-cto-jtbb75hop
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a27-cto-jtbb75hop
N=$1; G=$2; W=$3; SRCB=${SRCB:-$WT/programs/pump}
rm -rf $OUT/var/$N; rsync -a --exclude target $SRCB/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs "$G" <<'PY' || exit 1
import sys,runpy
f,g=sys.argv[1],sys.argv[2]; s=open(f).read(); n0=s.count('\n')
for a,b in runpy.run_path(g)['EDITS']:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'line count changed'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/work$W
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/t2/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > $OUT/ir/caplog_$N.txt 2>&1
if [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; tail -5 $OUT/ir/caplog_$N.txt >&2; grep -h -m2 -A6 "^error" $OUT/ir/cap_$N/*.log >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N $OUT/var/$N
echo captured $N
