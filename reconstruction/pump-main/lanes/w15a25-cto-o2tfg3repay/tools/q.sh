#!/bin/bash
# q.sh <slot> <resfile> name:genes ... : sequential vr.sh (plain + IR-forced O + O312) runs on one slot
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay; S=$1; R=$2; shift 2
for x in "$@"; do n=${x%%:*}; g=${x#*:}; RES=$R bash $OUT/tools/vr.sh $n $g $S; done
echo "done $S $(date +%T)" >> $OUT/q$S.done
