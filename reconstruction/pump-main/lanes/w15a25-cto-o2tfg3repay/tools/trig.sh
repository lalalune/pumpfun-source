#!/bin/bash
# trig.sh <name> <genes> <slot>: capture + rx; inl.py (post-O3 outline map), ibfi (pre-inline BFI), calls, fr metrics -> trig.txt
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a25-cto-o2tfg3repay; cd $OUT
N=$1
bash tools/cv.sh "$@" >/dev/null 2>log_$N.err || { echo "$N $2 | COMPILE FAIL $(tail -3 log_$N.err|tr '\n' ' ')" >> ${RES:-trig.txt}; exit 1; }
I=$(python3 tools/inl.py rx/$N/m.ll | cut -c14-); B=$(python3 tools/thr.py ir/$N.ll 2>&1|tail -1); K=$(python3 tools/ncall.py rx/$N/fn.bin | cut -d' ' -f2-)
echo "$N $2 | $I | THR $B | $K | $(python3 tools/fr.py $N | tr '\n' ' ') | $(cat rx/$N/res.json)" >> ${RES:-trig.txt}
[ "$KEEP" = 1 ] || rm -f ir/$N.ll; rm -f rx/$N/m.ll rx/$N/m.o
