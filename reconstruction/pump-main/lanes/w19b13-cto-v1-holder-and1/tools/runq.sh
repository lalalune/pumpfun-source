#!/bin/bash
# runq.sh <slot> name:genes name:genes ...  : sequential captures on one work dir; results append to res/fx.jsonl
s=$1; shift
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1
for x in "$@"; do n=${x%%:*}; g=${x#*:}; python3 $OUT/tools/g.py $n "$g" && bash $OUT/tools/cap.sh $n $s 2>&1 | tail -1 | cut -c1-200; python3 $OUT/tools/rg.py $OUT/fx/$n/fn.bin $OUT/fx/m7/fn.bin 2>/dev/null | tee -a $OUT/res/rg.txt | cut -c1-400; done
