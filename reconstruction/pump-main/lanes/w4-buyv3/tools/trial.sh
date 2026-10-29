#!/bin/bash
# trial.sh <name> <edit.py>   (WORK=slot dir)
set -e
export PUMP_BUILD_SLOTS=10
NAME=$1; EDIT=$2
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-buyv3
BASESRC=${BASESRC:-$WT/programs/pump}
T=$WT/reconstruction
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w4-buyv3
BASEJ=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/final/out/score.json
SRC=$OUT/trials/$NAME; O=$OUT/out/$NAME
rm -rf $SRC $O; mkdir -p $SRC; rsync -a --exclude target $BASESRC/ $SRC/
python3 $EDIT $SRC
cd /tmp
python3 $OUT/oracle/capture.py $SRC ${WORK:-$OUT/work1} $O > $OUT/out-$NAME.log 2>&1 || true
if [ ! -f $O/unstripped.so ]; then grep -m8 -E '^error|error\[' $O/build.log $OUT/out-$NAME.log | head; echo "$NAME BUILD-FAILED"; exit 1; fi
python3 $T/harness/score.py $O/unstripped.so --baseline $BASEJ --json $O/score.json --quiet >/dev/null
S=$(python3 -c "import json;d=json.load(open('$O/score.json'))['summary'];print('SCORE',d['normalized'],d['raw'],'g',d['gains'],'l',d['losses'],'rg',d['raw_gains'][:3],'rl',d['raw_losses'][:3])")
M=$(python3 $T/harness/target_metric.py $O/unstripped.so 0x147ba0 --sym 'trade::buy$' | tail -1 | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('BUY',d['cand_bytes'],d['ratio'],d['calls_candidate'])")
python3 $OUT/oracle/slim.py $O/pump_recovered.ll 5trade3buy17h $O/buy.ll
R=$(cd $O && ODIR=$O TAG=o python3 $OUT/oracle/oracle2.py buy.ll 5trade3buy17h)
echo "$NAME | $S | $M | $R"
