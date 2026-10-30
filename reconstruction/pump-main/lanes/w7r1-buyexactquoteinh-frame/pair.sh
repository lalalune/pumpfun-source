#!/bin/bash
# pair.sh n1 [n2]: run up to two trials in parallel (work dirs A,B)
source ~/.cache/pumpfun-reconstruction/lanes/w7r1-buyexactquoteinh-frame/env.sh
(WS=A $OUT/scripts/t.sh $1 > $OUT/out/$1.res 2>&1) &
[ -n "$2" ] && (WS=B $OUT/scripts/t.sh $2 > $OUT/out/$2.res 2>&1) &
wait; cat $OUT/out/$1.res; [ -n "$2" ] && cat $OUT/out/$2.res
for n in $1 $2; do echo "$n hunks: $(grep -c '^[-+] ' $OUT/out/$n.diff 2>/dev/null)"; done
