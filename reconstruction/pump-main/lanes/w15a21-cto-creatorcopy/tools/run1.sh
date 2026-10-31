#!/bin/bash
# run1.sh <name> <genes> <slot>: capture (cv.sh) + plain fr metrics -> res.txt
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a21-cto-creatorcopy; cd $OUT
N=$1
bash tools/cv.sh "$@" >/dev/null 2>log_$N.err || { echo "$N $2 | COMPILE FAIL $(tail -3 log_$N.err|tr '\n' ' ')" >> ${RES:-res.txt}; exit 1; }
echo "$N $2 | $(python3 tools/fr.py $N | tr '\n' ' ') | $(cat rx/$N/res.json) " >> ${RES:-res.txt}
[ "$KEEP" = 1 ] || rm -f ir/$N.ll; rm -f rx/$N/m.ll rx/$N/m.o
