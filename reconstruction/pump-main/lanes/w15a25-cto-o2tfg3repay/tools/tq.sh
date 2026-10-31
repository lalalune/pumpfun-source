#!/bin/bash
# tq.sh <slot> name:genes ... : sequential capt.sh runs (one build each) after waiting for the slot's previous work
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay; S=$1; shift
while pgrep -f "capraw.py .*lanes/w15a25-cto-o2tfg3repay/.*work$S " >/dev/null; do sleep 3; done
for x in "$@"; do n=${x%%:*}; g=${x#*:}; bash $OUT/tools/capt.sh $n $g $S; done
echo "done $S $(date +%T)" >> $OUT/tq$S.done
