#!/bin/bash
# trial.sh NAME EDIT.py [W]: copy crate, apply edit(text)->text to multi_hop_curve_swap.rs (line count kept),
# build with IR(+MIR) capture in work$W, report target metric + llc-oracle + GEP placement.
set -u
n=$1; ed=$2; w=${3:-0}
OUT=${LANE_OUT:-$HOME/.cache/pumpfun-reconstruction/lanes/w12b01-hop-gep}
T=$(cd "$(dirname "$0")" && pwd)
WT=$(cd "$T/../../../../.." && pwd)
SRC=${SRCBASE:-$WT/programs/pump}
export PUMP_BUILD_SLOTS=10
rm -rf $OUT/var/$n; mkdir -p $OUT/var/$n; rsync -a --exclude target $SRC/ $OUT/var/$n/
python3 - "$OUT/var/$n/src/multi_hop_curve_swap.rs" "$ed" <<'P' || exit 1
import sys,runpy
import os
p=sys.argv[1]; t=open(p).read(); n0=t.count('\n'); ns=runpy.run_path(sys.argv[2]); t2=ns['edit'](t)
assert t2!=t, 'edit no-op'
assert t2.count('\n')==n0, 'line count changed %d->%d'%(n0,t2.count('\n'))
open(p,'w').write(t2)
if 'extra' in ns:
    d=os.path.dirname(p)
    for f,fn in ns['extra'].items():
        q=os.path.join(d,f); s=open(q).read(); m0=s.count('\n'); s2=fn(s); assert s2!=s, f+' no-op'; assert s2.count('\n')==m0, f+' line count changed'; open(q,'w').write(s2)
P
mkdir -p $OUT/t/$n
python3 $T/capir.py --src $OUT/var/$n --work $OUT/work$w --out $OUT/t/$n ${MIR:+--mir} > $OUT/t/$n/cap.json 2>&1
if ! grep -q '"ok": true' $OUT/t/$n/cap.json; then echo "$n BUILD FAIL"; grep -E "^error|^ *--> " $OUT/t/$n/build.log | head -8; exit 1; fi
python3 $WT/reconstruction/harness/target_metric.py $OUT/t/$n/unstripped.so 0x5b3b0 --sym 'multi_hop_curve::swap_hop$' > $OUT/t/$n/hop.json 2>/dev/null
python3 -c "import json; d=json.loads(open('$OUT/t/$n/hop.json').readline()); print('$n', 'bytes', d['cand_bytes'], 'ratio', d['ratio'], 'slots', d.get('slots_diff'), 'calls', d['calls_candidate'])"
python3 $T/orc.py $OUT/t/$n/module.ll --name t_$n > /dev/null
python3 $T/gepwhere.py $OUT/orc/t_$n/sh.ll
