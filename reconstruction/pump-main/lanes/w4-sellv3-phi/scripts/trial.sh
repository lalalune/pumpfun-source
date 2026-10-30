#!/bin/bash
# trial.sh <name> <edit.py>   edit.py receives crate dir as argv[1]
set -e
export PUMP_BUILD_SLOTS=10
NAME=$1; EDIT=$2; BASESRC=${BASESRC:-/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-sellv3-phi/programs/pump}
TOOLS=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w4-sellv3-phi/reconstruction
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi
BASEJ=/private/tmp/claude-501/-Users-shawwalters-Documents-Codex-2026-10-24-pumpfun-source/4381c718-211a-406c-9278-6119c4649998/scratchpad/w3/final/out/score.json
SRC=$OUT/trials/$NAME
rm -rf $SRC; mkdir -p $SRC; rsync -a --exclude target $BASESRC/ $SRC/
python3 $EDIT $SRC
diff -u $BASESRC/src $SRC/src > $OUT/trials/$NAME.patch || true
cd /tmp
python3 $TOOLS/harness/fastbuild.py --src $SRC --work ${WORK:-$OUT/work} --out $OUT/out/$NAME > $OUT/out-$NAME.log 2>&1 || { tail -30 $OUT/out-$NAME.log; echo BUILD-FAILED; exit 1; }
shasum -a 256 $OUT/out/$NAME/unstripped.so | cut -c1-16
python3 $TOOLS/harness/target_metric.py $OUT/out/$NAME/unstripped.so 0x14a8a8 --sym 'trade::sell$' | python3 -c "import sys,json;d=json.loads(sys.stdin.read().strip().splitlines()[-1]);print(d['window'],d['cand_bytes'],d['ratio'],d.get('slots_diff'),d['calls_candidate'],d['normalized_equal'])"
python3 $TOOLS/harness/win.py show 0x14a8a8 --cand $OUT/out/$NAME/unstripped.so --sym 'trade::sell$' 2>/dev/null | grep -c '^[-+] ' || true
if [ -n "$SCORE" ]; then
python3 $TOOLS/harness/score.py $OUT/out/$NAME/unstripped.so --baseline $BASEJ --json $OUT/out/$NAME/score.json --quiet | tail -3
python3 -c "import json;d=json.load(open('$OUT/out/$NAME/score.json'))['summary'];print('SCORE',d['normalized'],d['raw'],'gains',d['gains'],'losses',d['losses'],d['raw_gains'],d['raw_losses'])"
fi
