#!/bin/bash
# q2.sh <slot> name:genes ... : sequential cap.sh (raw-IR capture + V + rx) then ev.sh per cell
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a22-cto-s3outline; S=$1; shift
for x in "$@"; do n=${x%%:*}; g=${x#*:}; bash $OUT/tools/cap.sh $n "$g" $S >> $OUT/q$S.log 2>&1 && bash $OUT/tools/ev.sh $n > /dev/null 2>&1; echo "ev $n $(date +%T)" >> $OUT/q$S.log; done
echo "qdone $S $(date +%T)" >> $OUT/q$S.log
