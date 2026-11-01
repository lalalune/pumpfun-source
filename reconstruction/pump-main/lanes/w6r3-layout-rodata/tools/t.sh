#!/bin/bash
# t.sh NAME [src]
N=$1; W=./worktrees/w6r3-layout-rodata; SRC=${2:-$W/programs/pump}
O=~/.cache/pumpfun-reconstruction/lanes/w6r3-layout-rodata; H=$W/reconstruction/harness
BASEJ=./9ebf44b6-961d-4889-839c-f928372efc77/scratchpad/w6/verify-r2/score.json
export PUMP_BUILD_SLOTS=10
python3 $H/fastbuild.py --src $SRC --work ${WORK:-$O/work} --out $O/out/$N > $O/out/$N.fb.json 2>&1 || { grep -E "^error" -A6 $O/out/$N/build.log | head -30; echo BUILD-FAIL; exit 1; }
grep -o '"unstripped_sha256": "[0-9a-f]*"' $O/out/$N.fb.json
python3 $H/score.py $O/out/$N/unstripped.so --baseline $BASEJ --json $O/out/$N/score.json --quiet | tail -1
python3 -c "
import json;d=json.load(open('$O/out/$N/score.json'))['summary'];print('norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',d['losses'],'rawgains',len(d['raw_gains']),'rawlosses',d['raw_losses'])"
python3 $H/target_metric.py $O/out/$N/unstripped.so 0x22a10 --sym 'admin_cto7execute17' 2>&1 | tail -3
