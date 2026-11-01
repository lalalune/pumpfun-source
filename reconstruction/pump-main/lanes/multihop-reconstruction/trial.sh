#!/bin/bash
# trial.sh <name> [srcdir]
set -e
export PUMP_BUILD_SLOTS=10
TOOLS=./worktrees/restore/reconstruction
WT=./worktrees/multihop-reconstruction
OUT=~/.cache/pumpfun-reconstruction/lanes/multihop-reconstruction
BASE=~/.cache/pumpfun-reconstruction/baseline-main-d2cb88d
N=$1; SRC=${2:-$WT/programs/pump}
python3 $TOOLS/harness/fastbuild.py --src $SRC --work $OUT/work-$N --out $OUT/out/$N > $OUT/out-$N.log 2>&1 || { tail -30 $OUT/out-$N.log; exit 1; }
rm -rf $OUT/work-$N
python3 $TOOLS/harness/score.py $OUT/out/$N/unstripped.so --baseline $BASE/score.json --json $OUT/out/$N/score.json --quiet
python3 $TOOLS/harness/target_metric.py $OUT/out/$N/unstripped.so 0x5b3b0 --sym 'swap_hop$'
python3 $OUT/bin/calls.py $TOOLS/harness $OUT/out/$N/unstripped.so > $OUT/out/$N/calls.txt
python3 $TOOLS/harness/coords.py fn $(python3 -c "
import sys; sys.path.insert(0,'$TOOLS/harness'); import coords
from pathlib import Path
print(hex(next(s for s,n,nm in coords.candidate_functions(Path('$OUT/out/$N/unstripped.so')) if '8swap_hop17h' in nm)))") --cand $OUT/out/$N/unstripped.so | python3 -c "import json,sys; print('coords',[(hex(d['slot']),d['line']) for d in json.load(sys.stdin)])"
echo "closures: $(grep closure $OUT/out/$N/calls.txt | awk '{print $NF}' | tr -d '[]' | tr '\n' ' ')"
python3 $WT/reconstruction/pump-main/lanes/callgraph-census/census.py --cand $OUT/out/$N/unstripped.so --only 0x5b3b0 --json $OUT/out/$N/census.json --md $OUT/out/$N/census.md 2>&1 | tail -1
