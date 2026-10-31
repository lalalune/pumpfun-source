#!/bin/bash
# two.sh <name> <genes> <slot>: capture variant, score as-is and on base O (noinline 307/312); keep IR only if KEEP=1
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a126-cto-origfill; cd $OUT
tools/cv.sh $1 $2 $3 > log_$1.txt 2>&1 || { echo "$1 $2 | COMPILE FAIL $(tail -3 log_$1.txt|tr '\n' ' ')" >> ${RES:-results.txt}; exit 1; }
python3 tools/rx.py ${1}_O ed/ni.py --base ir/$1.ll > /dev/null 2>&1
echo "$1 $2 | $(python3 tools/fr.py $1 ${1}_O | tr '\n' ' ') | $(cat rx/$1/res.json) $(cat rx/${1}_O/res.json 2>/dev/null)" >> ${RES:-results.txt}
[ "$KEEP" = 1 ] || rm -f ir/$1.ll
