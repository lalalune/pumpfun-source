#!/bin/bash
# runlist.sh <listfile> <vdir> <res.jsonl> <slot>: capture+oracle each variant name in list (one worker)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a73-cto-autospell
L=$1; V=$2; R=$3; W=$4
while read n; do
  [ -z "$n" ] && continue
  grep -q "\"name\": \"$n\"" $R 2>/dev/null && continue
  line=$(bash $OUT/tools/capvar.sh $n $V/$n.py $W 2>/dev/null | tail -1)
  [ -z "$line" ] && line="{\"name\":\"$n\",\"error\":\"nooutput\"}"
  echo "$line" >> $R
  rm -f $OUT/ir/$n.ll $OUT/rx/$n/m.ll $OUT/rx/$n/m.o; rm -rf $OUT/var/$n
done < $L
