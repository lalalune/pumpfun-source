#!/bin/bash
# t2.sh <name> <work-suffix> <rustc args...>: main-crate-only flags
N=$1; WK=$2; shift 2
WT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel); R=$WT/reconstruction
L=$HOME/.cache/pumpfun-reconstruction/lanes/w8-profile-flags
S=$L/src/$N; mkdir -p $S; rsync -a --delete --exclude /target/ ${SRCDIR:-$WT/programs/pump}/ $S/
PUMP_BUILD_SLOTS=10 python3 "$(dirname "$0")/mainonly.py" $S $L/work-$WK $L/out/$N "$@" > $L/out-$N.build.json 2>&1
rm -rf $S
if ! grep -q '"ok": true' $L/out-$N.build.json; then echo "$N BUILD FAILED $(grep -m1 -E 'exceeded max offset|^error' $L/out/$N/build.log | cut -c1-160)"; exit 1; fi
python3 $R/harness/score.py $L/out/$N/unstripped.so --baseline ${BASESCORE:-$L/out/base/score.json} --json $L/out/$N/score.json --quiet > /dev/null 2>&1
python3 - $L/out/$N/score.json $N <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))['summary']
print(sys.argv[2],'sha',d['candidate_sha256'][:12],'norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',len(d['losses']),d['losses'][:6],'rawg',len(d['raw_gains']),'rawl',len(d['raw_losses']))
PY
python3 $R/harness/target_metric.py $L/out/$N/unstripped.so 0x80df8 0x1e7c0 0x22a10 0x5b3b0 0x72810 0x13b9b8 0x13f630 0x1489f8 --top 1 2>/dev/null | python3 -c '
import sys,json
print("  "+" ".join("%s:%s/%s%s"%(d["window"][2:],d["cand_bytes"],d["ratio"],(":sd%d"%d["slots_diff"]) if "slots_diff" in d else "") for d in map(json.loads,sys.stdin)))'
