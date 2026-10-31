#!/bin/bash
# batch.sh <slot> name:genes ...  sequential on one slot
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a21-cto-creatorcopy; S=$1; shift
for x in "$@"; do n=${x%%:*}; g=${x#*:}; bash $OUT/tools/run1.sh $n $g $S; done
echo done >> $OUT/bg$S.done
