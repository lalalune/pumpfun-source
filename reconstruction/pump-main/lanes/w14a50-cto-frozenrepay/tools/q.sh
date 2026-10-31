#!/bin/bash
# q.sh <list> <res.jsonl> <worker idx> <nworkers>
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay
L=$1; R=$2; W=$3; N=$4; i=0
while read n; do
  if [ $((i % N)) -eq $W ]; then
    if ! grep -q "\"name\": \"$n\"" $R 2>/dev/null; then
      out=$(bash $O/tools/capvar.sh $n $O/e/$n.py $W 2>/dev/null | tail -1)
      [ -z "$out" ] && out="{\"name\": \"$n\", \"error\": \"compile\"}"
      echo "$out" >> $R
      rm -rf $O/var/$n $O/ir/$n.ll $O/rx/$n/m.ll $O/rx/$n/m.o
    fi
  fi
  i=$((i+1))
done < $L
