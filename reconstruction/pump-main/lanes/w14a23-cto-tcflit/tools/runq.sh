#!/bin/bash
# runq.sh <slot> <listfile> <resfile> <edir>
cd ~/.cache/pumpfun-reconstruction/lanes/w14a23-cto-tcflit
while read n; do
  [ -z "$n" ] && continue
  r=$(bash tools/capvar.sh $n $4/$n.py $1 2>/dev/null | tail -1)
  [ -z "$r" ] && r="{\"name\":\"$n\",\"error\":\"none\"}"
  echo "$r" >> $3
  rm -rf var/$n rx/$n/m.o ir/$n.ll
done < $2
