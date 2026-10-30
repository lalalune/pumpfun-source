#!/bin/bash
# capvar.sh <name> <edits.py|-> <slot>: copy lane crate, apply EDITS, capture raw IR + MIR, run rx oracle
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3
WT=${CRATE:-/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3/basecrate}
N=$1; P=$2; W=$3
mkdir -p $OUT/ir $OUT/mir
rm -rf $OUT/var/$N; rsync -a --exclude target $WT/ $OUT/var/$N/
if [ "$P" != "-" ]; then
python3 - $OUT/var/$N/src/creator/admin_cto.rs $P <<'PY' || exit 1
import sys
f,p=sys.argv[1],sys.argv[2]; s=open(f).read(); g={}; exec(open(p).read(),g)
n0=s.count('\n')
for a,b in g["EDITS"]:
    c=s.count(a); assert c==1,(c,a[:120]); s=s.replace(a,b)
assert s.count('\n')==n0
open(f,'w').write(s)
PY
fi
export PUMP_BUILD_SLOTS=10
rm -f $OUT/work$W/target*/*/release/deps/pump_recovered*.ll $OUT/work$W/target*/*/release/deps/pump_recovered*.mir
python3 $OUT/tools/capboth.py $OUT/var/$N $OUT/work$W $OUT/ir/cap_$N > /dev/null 2>&1
if grep -q '^error' $OUT/ir/cap_$N/build.log 2>/dev/null || [ ! -f $OUT/ir/cap_$N/raw.ll ]; then echo "{\"name\":\"$N\",\"error\":\"compile\"}"; grep -m2 -A3 '^error' $OUT/ir/cap_$N/build.log >&2; rm -rf $OUT/ir/cap_$N; exit 1; fi
mv $OUT/ir/cap_$N/raw.ll $OUT/ir/$N.ll
python3 $OUT/tools/exmir.py $OUT/ir/cap_$N/opt.mir $OUT/mir/$N.mir 2>/dev/null
rm -rf $OUT/ir/cap_$N
cd $OUT && RX_OUT=$OUT python3 tools/rx.py $N --base ir/$N.ll --keep | tail -1
