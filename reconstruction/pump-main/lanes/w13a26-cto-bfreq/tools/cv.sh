#!/bin/bash
# cv.sh <name> <edits.py> <slot 0|1>: crate copy + exact source EDITS (newline count kept) -> raw-IR capture (one build
# slot) -> opt -O3 -> extract execute -> llc oracle (bwx.py). Prints one JSON line; keeps ir/<name>.ex.ll. Experiment only.
LANE=w13a26-cto-bfreq
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/$LANE
WT=/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/$LANE
T=$WT/reconstruction/pump-main/lanes/$LANE/tools
RB=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin
N=$1; P=$2; W=$3
mkdir -p $OUT/var $OUT/ir
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/programs/pump/ $OUT/var/$N/
python3 - $OUT/var/$N/src/creator/admin_cto.rs $P <<'PY' || { echo "{\"name\":\"$N\",\"error\":\"edit\"}"; exit 1; }
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
for a,b in g["EDITS"]:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0,'newlines'
open(f,'w').write(s)
PY
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $T/capraw.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > /dev/null 2>&1
if grep -q '^error' $OUT/ir/cap_$N/build.log || [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -m3 -A6 '^error' $OUT/ir/cap_$N/build.log >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
$RB/opt -O3 $OUT/ir/cap_$N/raw.ll -S -o $OUT/ir/cap_$N/o3.ll
S=$(grep -o '^define[^@]*@_ZN14pump_recovered9admin_cto7execute[A-Za-z0-9_]*' $OUT/ir/cap_$N/o3.ll | sed 's/.*@//')
$RB/opt -passes='internalize,globaldce' -internalize-public-api-list=$S $OUT/ir/cap_$N/o3.ll -S -o $OUT/ir/$N.ex.ll
rm -rf $OUT/ir/cap_$N $OUT/var/$N
python3 $T/bwx.py run $OUT/ir/$N.ex.ll '' | sed "s/^{/{\"name\":\"$N\",/" | tee -a $OUT/cv.jsonl
