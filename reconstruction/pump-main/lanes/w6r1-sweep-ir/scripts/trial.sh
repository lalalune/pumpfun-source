#!/bin/bash
# trial.sh NAME file.rs [score]
set -e
OUT=~/.cache/pumpfun-reconstruction/lanes/w6r1-sweep-ir
T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r1-sweep-ir/reconstruction/harness
BASEJ=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/9ebf44b6-961d-4889-839c-f928372efc77/scratchpad/w6/base/score.json
N=$1; F=$2
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/srcs; rm -rf $OUT/srcs/$N; rsync -a --exclude target $OUT/src0/ $OUT/srcs/$N/
cp $F $OUT/srcs/$N/src/sweep_fees.rs
python3 $OUT/scripts/capture.py $OUT/srcs/$N $OUT/work-${W:-0} $OUT/out/$N $LLVMARGS > $OUT/out/$N.cap.json 2>&1 || { tail -30 $OUT/out/$N/build.log; echo BUILD-FAIL; exit 1; }
grep -q '"ok": true' $OUT/out/$N.cap.json || { grep -m5 -A5 'error' $OUT/out/$N/build.log; echo BUILD-FAIL; exit 1; }
python3 $OUT/scripts/mkone.py $OUT/out/$N/pump_recovered.ll $OUT/out/$N/one.ll
python3 $OUT/scripts/oracle.py $OUT/out/$N/one.ll $N
python3 $T/target_metric.py $OUT/out/$N/unstripped.so 0x72810 --sym 'sweep.*execute'
if [ "$3" = score ]; then python3 $T/score.py $OUT/out/$N/unstripped.so --baseline $BASEJ --json $OUT/out/$N/score.json --quiet | tail -5; fi
[ -n "$KEEP" ] || rm -f $OUT/out/$N/pump_recovered.ll $OUT/out/$N/pump_recovered.bc
if [ -n "$LLVMARGS" ]; then python3 $OUT/scripts/bfi.py $OUT/out/$N/build.log $OUT/out/$N/fn.ll | grep -i "clone\|admit\|transfer_to" | cut -c1-60; fi
