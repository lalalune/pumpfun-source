#!/bin/bash
# batch.sh <results.jsonl> names... : 2 workers; capture+rx then px (fm/sk/err)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a67-cto-h7src
export RX_OUT=$OUT
R=$1; shift
run(){ w=$1; shift; for n in "$@"; do
  r=$(bash $OUT/tools/capvar.sh $n $OUT/e/$n.py $w 2>$OUT/err_$n.txt | tail -1); [ -z "$r" ] && r="{\"name\":\"$n\",\"error\":\"$(head -c 300 $OUT/err_$n.txt | tr '\n"' ' _')\"}"
  p=""; [ -f $OUT/rx/$n/m.ll ] && p=$(python3 $OUT/tools/px.py $OUT/rx/$n/m.ll 2>/dev/null | tail -1)
  echo "$r $p" >> $R; rm -rf $OUT/var/$n $OUT/ir/$n.ll $OUT/rx/$n/m.o
done; }
A=(); B=(); i=0; for n in "$@"; do if [ $((i%2)) = 0 ]; then A+=($n); else B+=($n); fi; i=$((i+1)); done
run 0 "${A[@]}" & run 1 "${B[@]}" & wait
echo DONE >> $R
