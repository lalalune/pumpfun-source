#!/bin/bash
# screen.sh <slot> name... : run capvar for ev/<name>.py sequentially, append results to screen.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a121-cto-delwin
W=$1; shift
for n in "$@"; do
  r=$(cd $OUT && bash tools/capvar.sh $n ev/$n.py $W 2>$OUT/ir/$n.err | tail -1)
  [ -z "$r" ] && r="{\"name\":\"$n\",\"error\":\"none\"}"
  echo "$r" >> $OUT/screen.jsonl
  rm -f $OUT/ir/$n.ll; rm -rf $OUT/var/$n
done
