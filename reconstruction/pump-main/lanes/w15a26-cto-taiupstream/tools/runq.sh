#!/bin/bash
# runq.sh <slot> <names...>: capture+rx each variant sequentially into e/<name>.res
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a26-cto-taiupstream
W=$1; shift
for n in "$@"; do $OUT/tools/capvar.sh $n $OUT/e/$n.py $W > $OUT/e/$n.res 2>$OUT/e/$n.err; echo "$n $(cat $OUT/e/$n.res)"; done
