#!/bin/bash
# runq.sh <slot> <listfile> <resfile>: run capvar on every name in the list whose index%2==slot
cd ~/.cache/pumpfun-reconstruction/lanes/w14a34-cto-curvetail
s=$1; i=0
while read n; do
  if [ $((i%2)) -eq $s ]; then r=$(bash tools/capvar.sh $n e/$n.py $s 2>/dev/null | tail -1); [ -z "$r" ] && r="{\"name\":\"$n\",\"error\":\"none\"}"; echo "$r" >> $3; rm -rf var/$n rx/$n/m.ll ir/$n.ll; fi
  i=$((i+1))
done < $2
