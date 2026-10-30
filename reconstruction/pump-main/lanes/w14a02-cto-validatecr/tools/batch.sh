#!/bin/bash
# batch.sh name1 name2 ...: run trials 2 at a time (slots 0/1), composite names = genes joined by _
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a02-cto-validatecr
run(){ n=$1; s=$2; printf 'import sys;sys.path.insert(0,"%s/e");import gen\nEDITS=gen.mkf("%s")\n' $O $n > $O/e/t_$n.py; bash $O/tools/capvar.sh $n $O/e/t_$n.py $s > $O/rx/$n.res 2>$O/rx/$n.err; [ -f $O/rx/$n/m.o ] && python3 $O/tools/chunk.py $O/rx/$n/m.o >> $O/chunks.jsonl; cat $O/rx/$n.res >> $O/results.jsonl; }
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  run ${a[$i]} 0 & [ $((i+1)) -lt ${#a[@]} ] && run ${a[$((i+1))]} 1 & wait; i=$((i+2))
done
