#!/bin/bash
# trial.sh <name> <patch.py> <workslot>  (diagnostic source trial; patch.py edits <crate>/src/trade_v3.rs text via edit(s))
set -e
W=./worktrees/w7r1-v3buycosts-frame
OUT=~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-frame
N=$1; P=$2; S=${3:-a}
export PUMP_BUILD_SLOTS=10
rm -rf $OUT/src/$N; mkdir -p $OUT/src/$N
rsync -a --exclude target $W/programs/pump/ $OUT/src/$N/
python3 -c "
import runpy,sys
p='$OUT/src/$N/src/trade_v3.rs'; s=open(p).read(); s2=runpy.run_path('$P')['edit'](s); assert s2!=s,'no change'
assert s2.count('\n')==s.count('\n'), 'line count changed %d'%(s2.count('\n')-s.count('\n'))
open(p,'w').write(s2)"
python3 $W/reconstruction/harness/fastbuild.py --src $OUT/src/$N --work $OUT/work-$S --out $OUT/out/$N > $OUT/out-$N.log 2>&1 || { echo "$N BUILD FAIL"; tail -30 $OUT/out/$N/build.log | grep -E '^error' -A6 | head -30; exit 1; }
python3 $W/reconstruction/harness/score.py $OUT/out/$N/unstripped.so --baseline $OUT/out/base/score.json --json $OUT/out/$N/score.json --quiet | python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print('$N', 'norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',d['losses'],'rawg',len(d['raw_gains']),'rawl',d['raw_losses'], 'sha',d['candidate_sha256'][:12])"
python3 $W/reconstruction/harness/target_metric.py $OUT/out/$N/unstripped.so 0x80df8 --sym 'v3_buy_costs' --top 1
