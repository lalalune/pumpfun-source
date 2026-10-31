#!/bin/bash
# batch.sh <res.jsonl> names... : 2-worker capvar queue; appends rx result + px fm/sk/err; cleans var/ir
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a112-cto-irorder14
R=$1; shift
run(){ n=$1; w=$2; r=$(bash $O/tools/capvar.sh $n $O/gen/$n.py $w 2>$O/ir/err_$n.txt | tail -1)
  p=$(python3 $O/tools/px.py $O/rx/$n/m.ll 2>/dev/null | tail -1)
  echo "{\"n\":\"$n\",\"rx\":$r,\"px\":${p:-null}}" >> $R; rm -rf $O/var/$n; rm -f $O/rx/$n/m.bin; }
i=0; for n in "$@"; do run $n $((i%2)) & i=$((i+1)); if [ $((i%2)) = 0 ]; then wait; fi; done; wait
