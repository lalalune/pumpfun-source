#!/bin/bash
# batch2.sh <res.jsonl> name...  : capvar runs two at a time (slots 0/1); edits at ed/<name>.py
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a122-cto-shareclonealias
R=$1; shift; i=0
for n in "$@"; do
  ( r=$(bash $OUT/tools/capvar.sh $n $OUT/ed/$n.py $((i%2)) 2>>$OUT/batch.err); echo "$r" >> $R; rm -rf $OUT/var/$n ) &
  i=$((i+1)); if (( i%2==0 )); then wait; fi
done; wait
