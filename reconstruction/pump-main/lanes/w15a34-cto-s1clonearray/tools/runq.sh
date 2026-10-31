#!/bin/bash
# runq.sh <slot> <names...>: capture each variant (ed/<name>.py) and append rx result to src.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a34-cto-s1clonearray
W=$1; shift
for N in "$@"; do
  t0=$(date +%s)
  R=$(bash $OUT/bin/capvar.sh $N $OUT/ed/$N.py $W 2>>$OUT/capvar.err)
  echo "$R" | tail -1 >> $OUT/src.jsonl
  echo "$(date +%T) $N $(($(date +%s)-t0))s $R" >> $OUT/runq.log
done
