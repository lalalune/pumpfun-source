#!/bin/bash
# capg.sh <name> <slot> [genes (g16 names joined by +)] [srcfile]: crate copy of WT + genes (or srcfile as admin_cto.rs), capopt post-opt IR -> cap/<name>/m.ll
set -u
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a30-shim-hk2stand
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a30-shim-hk2stand
n=$1; s=$2; g=${3:-}; src=${4:-}
v=$OUT/var/$n; rm -rf $v; mkdir -p $v
rsync -a --exclude target $WT/programs/pump/ $v/
if [ -n "$src" ]; then cp $src $v/src/creator/admin_cto.rs; fi
if [ -n "$g" ]; then python3 $OUT/tools/g16.py $v/src/creator/admin_cto.rs "$g" || { echo "{\"name\":\"$n\",\"err\":\"gene\"}"; exit 1; }; fi
w=$OUT/work$s; mkdir -p $w
for a in 1 2 3; do
  rm -rf $OUT/cap/$n
  PUMP_BUILD_SLOTS=10 python3 $OUT/tools/capopt.py $v $w $OUT/cap/$n > $OUT/cap/$n.log 2>&1
  [ -f $OUT/cap/$n/m.ll ] && break
  grep -qE 'ENFILE|Too many open files|temporarily unavailable|cannot lock ref' $OUT/cap/$n.log $OUT/cap/$n/build.log 2>/dev/null && { sleep 20; continue; }
  break
done
[ -f $OUT/cap/$n/m.ll ] || { echo "{\"name\":\"$n\",\"err\":\"capture failed\"}"; tail -30 $OUT/cap/$n/build.log 2>/dev/null | grep -m3 -A8 error; exit 1; }
rm -f $OUT/cap/$n/candidate.so $OUT/cap/$n/link.map
cp $v/src/creator/admin_cto.rs $OUT/cap/$n/admin_cto.rs; rm -rf $v
echo "{\"name\":\"$n\",\"ok\":true}"
