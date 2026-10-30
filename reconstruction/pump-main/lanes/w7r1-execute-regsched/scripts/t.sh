#!/bin/bash
# t.sh NAME file.rs [score]   (build crate copy with sweep_fees.rs replaced; IR capture + llc oracle + target metric)
OUT=~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-regsched
T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w7r1-execute-regsched/reconstruction/harness
N=$1; F=$2
export PUMP_BUILD_SLOTS=10
mkdir -p $OUT/srcs; rm -rf $OUT/srcs/$N; rsync -a --exclude target $OUT/src0/ $OUT/srcs/$N/
cp $F $OUT/srcs/$N/src/sweep_fees.rs
[ -n "$EXTRA" ] && bash -c "$EXTRA" _ $OUT/srcs/$N
python3 $OUT/scripts/capture.py $OUT/srcs/$N $OUT/work-${W:-0} $OUT/out/$N > $OUT/out/$N.cap.json 2>&1
grep -q '"ok": true' $OUT/out/$N.cap.json || { grep -m5 -A7 '^error' $OUT/out/$N/build.log; echo BUILD-FAIL; exit 1; }
python3 $OUT/scripts/mkone.py $OUT/out/$N/pump_recovered.ll $OUT/out/$N/one.ll
python3 $OUT/scripts/oracle.py $OUT/out/$N/one.ll $N
python3 $OUT/scripts/fm.py $N
python3 $T/target_metric.py $OUT/out/$N/unstripped.so 0x72810 --sym 'sweep.*execute' --top 1
if [ "$3" = score ]; then python3 $T/score.py $OUT/out/$N/unstripped.so --baseline $OUT/out/base/score.json --json $OUT/out/$N/score.json --quiet | python3 -c "import json,sys;d=json.load(sys.stdin);print('SCORE',d['normalized'],d['raw'],'gains',d['gains'],'losses',d['losses'],'rawg',d['raw_gains'],'rawl',d['raw_losses'])"; fi
[ -f $OUT/out/$N/pump_recovered.mir ] && python3 $OUT/scripts/xmir.py $OUT/out/$N/pump_recovered.mir > $OUT/out/$N/exec.mir && rm $OUT/out/$N/pump_recovered.mir
rm -f $OUT/out/$N/pump_recovered.ll $OUT/out/$N/pump_recovered.bc
rm -rf $OUT/srcs/$N
