#!/bin/bash
# capsrc.sh <name> <crate_dir> <slot>: capture raw IR of an existing crate dir, run rx oracle
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a22-cto-valslot
N=$1; SRC=$2; W=$3
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll
python3 $OUT/tools/capraw.py $SRC $OUT/work$W $OUT/ir/cap_$N > /dev/null 2>&1
if grep -q '^error' $OUT/ir/cap_$N/build.log || [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -m2 -A3 '^error' $OUT/ir/cap_$N/build.log >&2; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll; rm -rf $OUT/ir/cap_$N
cd $OUT && python3 tools/rx.py $N --base ir/$N.ll | tail -1
