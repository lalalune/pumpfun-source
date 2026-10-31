#!/bin/bash
# q.sh <slot> name... : capvar each e/<name>.py, append result to res.jsonl, then irre --only %33 on its m.ll
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a41-cto-derefreread
S=$1; shift
for n in "$@"; do
  r=$(bash $OUT/tools/capvar.sh $n $OUT/e/$n.py $S 2>>$OUT/q$S.err | tail -1)
  echo "$r" >> $OUT/res.jsonl
  rm -rf $OUT/var/$n $OUT/ir/$n.ll
done
