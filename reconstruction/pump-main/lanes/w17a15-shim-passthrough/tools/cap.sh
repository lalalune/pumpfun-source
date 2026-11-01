#!/bin/bash
# cap.sh <name> <slot> [crate_dir]: overlay $OUT/src/<name>.rs as admin_cto.rs on a copy of WT crate, capture pre-opt IR, slim, score with fx
set -u
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w17a15-shim-passthrough
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a15-shim-passthrough
n=$1; s=$2; export LANE_OUT=$OUT
v=$OUT/var/$n; rm -rf $v; mkdir -p $v
rsync -a --exclude target $WT/programs/pump/ $v/
[ -f $OUT/src/$n.rs ] && cp $OUT/src/$n.rs $v/src/creator/admin_cto.rs
[ -f $OUT/src/$n.lib.rs ] && cp $OUT/src/$n.lib.rs $v/src/lib.rs
w=$OUT/work$s; mkdir -p $w; rm -f $w/target*/*/release/deps/pump_recovered*.ll
cap=$OUT/ir/cap_$n; rm -rf $cap
for a in 1 2 3; do
  PUMP_BUILD_SLOTS=10 python3 $OUT/tools/capraw.py $v $w $cap > $OUT/ir/cap_$n.log 2>&1
  [ -f $cap/raw.ll ] && break
  grep -qE 'ENFILE|Too many open files|temporarily unavailable|cannot lock ref' $OUT/ir/cap_$n.log $cap/build.log 2>/dev/null && { sleep 20; continue; }
  break
done
if [ ! -f $cap/raw.ll ]; then echo "{\"name\":\"$n\",\"err\":\"capture failed\"}" | tee -a $OUT/res/fx.jsonl; grep -m5 -A8 'error' $cap/build.log 2>/dev/null | head -40; exit 1; fi
mv $cap/raw.ll $OUT/ir/$n.ll; [ -f $cap/unstripped.so ] && cp $cap/unstripped.so $OUT/ir/$n.so; rm -rf $cap $v
SURV=$OUT/data/surv-1647da0.txt python3 $OUT/tools/preslim.py $OUT/ir/$n.ll $OUT/ir/$n.s.ll keep >/dev/null
[ "${KEEPRAW:-0}" = 1 ] || rm -f $OUT/ir/$n.ll
python3 $OUT/tools/fx.py $OUT/ir/$n.s.ll $n --keep | tee -a $OUT/res/fx.jsonl
