#!/bin/bash
# tqf.sh <slot> name:genes ... : capt.sh then rxf.sh (full oracle) per variant, deleting the raw IR afterwards
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay; S=$1; shift
while pgrep -f "capraw.py .*lanes/w15a25-cto-o2tfg3repay/.*work$S " >/dev/null; do sleep 3; done
for x in "$@"; do n=${x%%:*}; g=${x#*:}; bash $OUT/tools/capt.sh $n $g $S && bash $OUT/tools/rxf.sh $n; rm -f $OUT/ir/$n.ll; done
echo "done $S $(date +%T)" >> $OUT/tqf$S.done
