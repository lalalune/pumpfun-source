#!/bin/bash
# trial.sh <name> <work-suffix> <extra-rustflags> [profile-file]
set -u
NAME=$1; WK=$2; RF=$3; PROF=${4:-}
WT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
R=$WT/reconstruction; OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w8-profile-flags
SRC=$OUT/src/$NAME; mkdir -p $SRC
rsync -a --delete --exclude /target/ $WT/programs/pump/ $SRC/
if [ -n "$PROF" ]; then python3 - "$SRC/Cargo.toml" "$PROF" <<'PY'
import sys
p,f=sys.argv[1:]; s=open(p).read(); a=s.index('[profile.release]'); b=s.index('[workspace]')
open(p,'w').write(s[:a]+open(f).read().strip()+'\n\n'+s[b:])
PY
fi
export PUMP_BUILD_SLOTS=10 PUMP_EXTRA_RUSTFLAGS="$RF"
python3 $R/harness/fastbuild.py --src $SRC --work $OUT/work-$WK --out $OUT/out/$NAME > $OUT/out-$NAME.build.json 2>&1
if ! grep -q '"ok": true' $OUT/out-$NAME.build.json; then echo "$NAME BUILD FAILED"; tail -5 $OUT/out-$NAME.build.json; rm -rf $SRC; exit 1; fi
python3 $R/harness/score.py $OUT/out/$NAME/unstripped.so --baseline $OUT/out/base/score.json --json $OUT/out/$NAME/score.json --quiet > $OUT/out/$NAME/score.line 2>&1
python3 - $OUT/out/$NAME/score.json $NAME <<'PY'
import json,sys
d=json.load(open(sys.argv[1]))['summary']
print(sys.argv[2], 'sha',d['candidate_sha256'][:12],'norm',d['normalized'],'raw',d['raw'],'gains',d['gains'],'losses',len(d['losses']),d['losses'][:12],'rawgains',len(d['raw_gains']),'rawlosses',len(d['raw_losses']))
PY
python3 $R/harness/target_metric.py $OUT/out/$NAME/unstripped.so 0x80df8 0x1e7c0 0x22a10 0x5b3b0 0x72810 0x13b9b8 0x13f630 0x1489f8 --top 1 2>/dev/null | python3 -c '
import sys,json
print("  "+" ".join("%s:%s/%s%s"%(d["window"],d["cand_bytes"],d["ratio"],(":sd%d"%d["slots_diff"]) if "slots_diff" in d else "") for d in map(json.loads,sys.stdin)))'
rm -rf $SRC
