#!/bin/bash
# trial.sh NAME [srcdir]
N=$1; SRC=${2:-/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/programs/pump}
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w6r2-layout-rodata; H=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness; T=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/pump-main/lanes/layout-order-census/tools
S=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w3-raw-layout
BASE=${BASEJ:-/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/9ebf44b6-961d-4889-839c-f928372efc77/scratchpad/w6/verify-r1/score.json}
export PUMP_BUILD_SLOTS=10
python3 $H/fastbuild.py --src $SRC --work ${WORK:-$OUT/work} --out $OUT/out/$N > $OUT/out/$N.fb.json 2>&1 || { grep -E "^error" -A6 $OUT/out/$N/build.log | head -30; echo BUILD-FAIL; exit 1; }
grep -o '"unstripped_sha256": "[0-9a-f]*"' $OUT/out/$N.fb.json
python3 $H/score.py $OUT/out/$N/unstripped.so --baseline $BASE --json $OUT/out/$N/score.json --quiet | tail -2
(cd $T && python3 refine.py $OUT/out/$N/unstripped.so $OUT/out/$N/refined.json >/dev/null 2>&1)
python3 $S/scripts/metrics.py $S $OUT/out/$N/unstripped.so $OUT/out/$N/refined.json
python3 $S/scripts/datamis.py $OUT/out/$N/unstripped.so $OUT/out/$N/refined.json
python3 $S/scripts/paths.py $OUT/out/$N/unstripped.so 3
sed "s#/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/restore/reconstruction#/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction#g" $S/scripts/drr.py > $OUT/scripts/drr.py; python3 $OUT/scripts/drr.py $OUT/out/$N/unstripped.so | head -8
python3 -c "
import json;d=json.load(open('$OUT/out/$N/score.json'))['summary'];print('norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',d['losses'],'rawgains',d['raw_gains'],'rawlosses',d['raw_losses'])"
