#!/bin/bash
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a21-cto-creatorcopy; S=$1; shift
for x in "$@"; do n=${x%%:*}; g=${x#*:}; RES=$OUT/resO.txt bash $OUT/tools/vr.sh $n $g $S; done
echo done >> $OUT/bg$S.done
