#!/bin/bash
# runq.sh <slot> names...: run trials sequentially on work<slot>, append to res.txt
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a29-cto-hcbools
s=$1; shift
for n in "$@"; do bash $OUT/tools/trial.sh $n $OUT/edits/$n.py $s >> $OUT/res.txt 2>>$OUT/err.txt; done
