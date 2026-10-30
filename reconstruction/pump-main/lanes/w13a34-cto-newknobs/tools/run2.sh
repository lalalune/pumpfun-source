#!/bin/bash
# run2.sh <slot> <results.jsonl> names... : capture on slot (sequential), rx in background (max 2 per worker)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a34-cto-newknobs
W=$1; R=$2; shift 2
cd $O
dorx(){ n=$1; r=$(python3 tools/rx.py $n --base ir/$n.ll 2>>$O/t/$n.err | tail -1); [ -z "$r" ] && r="{\"name\":\"$n\",\"error\":\"rx\"}"; echo "$r" >> $R; rm -f ir/$n.ll; rm -rf var/$n rx/$n/m.ll; }
for n in "$@"; do
  if bash tools/capvar2.sh $n edits/$n.py $W 2>$O/t/$n.err; then
    while [ $(jobs -rp | wc -l) -ge 2 ]; do sleep 2; done
    dorx $n &
  else echo "{\"name\":\"$n\",\"error\":\"compile\"}" >> $R; rm -rf var/$n; fi
done
wait
echo DONE >> $R.done$W
