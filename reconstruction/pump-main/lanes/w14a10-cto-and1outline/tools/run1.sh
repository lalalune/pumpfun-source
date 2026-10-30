#!/bin/bash
# run1.sh <name> <slot>: one gene-composite trial (capture + rx + chunk)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a10-cto-and1outline
n=$1; s=$2
printf 'import sys;sys.path.insert(0,"%s/e");import gen\nEDITS=gen.mkf("%s")\n' $O $n > $O/e/t_$n.py
bash $O/tools/capvar.sh $n $O/e/t_$n.py $s > $O/rx/$n.res 2>$O/rx/$n.err
[ -f $O/rx/$n/m.o ] && python3 $O/tools/chunk.py $O/rx/$n/m.o >> $O/chunks.jsonl
cat $O/rx/$n.res >> $O/results.jsonl
