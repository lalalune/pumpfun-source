#!/bin/bash
# cap.sh <name> <genes a+b+c> <slot> [genefile]: copy the WT crate, apply genes, capture pre-opt IR, preslim, fx (+framemap)
set -u
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a16-shim-outlinerepay
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w17a16-shim-outlinerepay
n=$1; genes=$2; s=$3; gf=${4:-$OUT/tools/g16.py}; export LANE_OUT=$OUT
v=$OUT/var/$n; rm -rf $v; mkdir -p $v $OUT/ir $OUT/res
rsync -a --exclude target $WT/programs/pump/ $v/
if [ -f "$OUT/src/$n.rs" ]; then cp $OUT/src/$n.rs $v/src/creator/admin_cto.rs; fi
python3 $gf $v/src/creator/admin_cto.rs "$genes" || { echo "{\"name\":\"$n\",\"err\":\"gene apply failed\"}" | tee -a $OUT/res/fx.jsonl; exit 1; }
cp $v/src/creator/admin_cto.rs $OUT/src/$n.applied.rs
w=$OUT/work$s; mkdir -p $w; rm -f $w/target*/*/release/deps/pump_recovered*.ll
cap=$OUT/ir/cap_$n; rm -rf $cap
for a in 1 2 3; do
  PUMP_BUILD_SLOTS=10 python3 $OUT/tools/capraw.py $v $w $cap > $OUT/ir/cap_$n.log 2>&1
  [ -f $cap/raw.ll ] && break
  grep -qE 'ENFILE|Too many open files|temporarily unavailable|cannot lock ref' $OUT/ir/cap_$n.log $cap/build.log 2>/dev/null && { sleep 20; continue; }
  break
done
if [ ! -f $cap/raw.ll ]; then echo "{\"name\":\"$n\",\"err\":\"capture failed\"}" | tee -a $OUT/res/fx.jsonl; grep -m5 -A12 'error' $cap/build.log 2>/dev/null | head -60; exit 1; fi
mv $cap/raw.ll $OUT/ir/$n.ll; rm -rf $cap $v
SURV=$OUT/data/surv-1647da0.txt python3 $OUT/tools/preslim.py $OUT/ir/$n.ll $OUT/ir/$n.s.ll keep >/dev/null
rm -f $OUT/ir/$n.ll
python3 $OUT/tools/fx.py $OUT/ir/$n.s.ll $n --keep | tee -a $OUT/res/fx.jsonl
python3 $OUT/tools/framemap.py $OUT/fx/$n/m.ll > $OUT/fx/$n/frame.txt 2>/dev/null
rm -f $OUT/fx/$n/in.ll $OUT/fx/$n/o3.ll
