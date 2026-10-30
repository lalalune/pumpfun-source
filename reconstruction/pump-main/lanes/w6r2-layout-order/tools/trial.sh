#!/bin/bash
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-order
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w6r2-layout-order
B=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/9ebf44b6-961d-4889-839c-f928372efc77/scratchpad/w6/verify-r1
H=$WT/reconstruction/harness
n=$1; src=${2:-$WT/programs/pump}; work=${WORK:-$OUT/work}
export PUMP_BUILD_SLOTS=10
python3 $H/fastbuild.py --src $src --work $work --out $OUT/out/$n > $OUT/out/$n.build.log 2>&1 || { echo BUILD FAILED; grep -E "^error" -A6 $OUT/out/$n.build.log | head -30; exit 1; }
python3 $H/score.py $OUT/out/$n/unstripped.so --baseline ${BASEJ:-$B/score.json} --json $OUT/out/$n/score.json --quiet
python3 $OUT/tools/unm.py $OUT/out/$n/unstripped.so
shasum -a 256 $OUT/out/$n/unstripped.so | cut -c1-16
