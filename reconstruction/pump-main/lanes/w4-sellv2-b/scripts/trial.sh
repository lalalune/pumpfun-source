#!/bin/zsh
# trial.sh <name> <patch.py>  : copy src, apply patch (python edits sell_v2.rs via replace pairs), capture build, metric+oracle
source ~/.cache/pumpfun-reconstruction/lanes/w4-sellv2-b/env.sh
n=$1; p=$2
rm -rf $OUT/src/$n; mkdir -p $OUT/src/$n; rsync -a --exclude target $WT/programs/pump/ $OUT/src/$n/
python3 $OUT/scripts/applyp.py $p $OUT/src/$n || { echo PATCHFAIL; exit 1; }
python3 $OUT/scripts/capture.py $OUT/src/$n $OUT/work${3:-} $OUT/out/$n > $OUT/out/$n.log 2>&1
grep -q '"ok": true' $OUT/out/$n.log || { echo BUILDFAIL; grep -m5 "error" $OUT/out/$n/build.log $OUT/out/$n.log | head; exit 1; }
python3 $TOOLS/harness/target_metric.py $OUT/out/$n/unstripped.so 0x144508 --sym "$SYMRE"
SYM=$(grep -o 'define hidden { i64, ptr } @_ZN14pump_recovered14pump_recovered7sell_v2[^(]*' $OUT/out/$n/pump_recovered.ll | sed 's/.*@//') IRBASE=$OUT/out/$n/pump_recovered.ll Q=1 python3 $OUT/scripts/irx.py t_$n -
