#!/bin/bash
# trial.sh NAME [srcdir]
set -e
N=$1; SRC=${2:-/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-raw-layout/programs/pump}
OUT=~/.cache/pumpfun-reconstruction/lanes/w3-raw-layout
H=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction/harness
T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w3-raw-layout/reconstruction/pump-main/lanes/layout-order-census/tools
BASE=${BASEJSON:-/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout/out/main-b08fd90/score.json}
export PUMP_BUILD_SLOTS=10
WORK=${WORK:-$OUT/work}
python3 $H/fastbuild.py --src $SRC --work $WORK --out $OUT/out/$N > $OUT/out/$N.fb.json 2>&1 || { tail -30 $OUT/out/$N/build.log | grep -E "^error|-->" | head; echo BUILD-FAIL; exit 1; }
python3 $H/score.py $OUT/out/$N/unstripped.so --baseline $BASE --json $OUT/out/$N/score.json --quiet | tail -3
(cd $T && python3 refine.py $OUT/out/$N/unstripped.so $OUT/out/$N/refined.json >/dev/null 2>&1)
python3 $OUT/scripts/metrics.py $OUT $OUT/out/$N/unstripped.so $OUT/out/$N/refined.json
python3 $OUT/scripts/paths.py $OUT/out/$N/unstripped.so 3
python3 -c "
import json;d=json.load(open('$OUT/out/$N/score.json'))['summary'];print('norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',d['losses'],'rawgains',len(d['raw_gains']),'rawlosses',d['raw_losses'])"
