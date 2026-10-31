#!/bin/bash
# vr.sh <name> <genes> <slot>: capture; rx plain, _O (307/312 noinline), _O312 (312 only); fr tiers -> res line
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a144-cto-vinarm; cd $OUT
N=$1
bash tools/cv.sh "$@" >/dev/null 2>log_$N.err || { echo "$N $2 | COMPILE FAIL $(tail -3 log_$N.err|tr '\n' ' ')" >> ${RES:-res.txt}; exit 1; }
python3 tools/rx.py ${N}_O ed/ni.py --base ir/$N.ll > /dev/null 2>&1
NI=19 python3 tools/rx.py ${N}_O312 ed/ni.py --base ir/$N.ll > /dev/null 2>&1
echo "$N $2 | $(python3 tools/fr.py $N ${N}_O ${N}_O312 | tr '\n' ' ') | $(cat rx/$N/res.json) " >> ${RES:-res.txt}
[ "$KEEP" = 1 ] || rm -f ir/$N.ll; rm -f rx/$N*/m.ll rx/$N*/m.o
