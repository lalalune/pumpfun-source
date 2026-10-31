#!/bin/bash
# batch.sh name1 name2 ...: genes joined by '+'; 2 at a time
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra
GF=${GF:-$O/e/genes.py}
run(){ n=$1; s=$2; printf 'import sys;sys.path.insert(0,"%s");import importlib.util as u\nsp=u.spec_from_file_location("g","%s");g=u.module_from_spec(sp);sp.loader.exec_module(g)\nEDITS=sum((g.G[x] for x in "%s".split("+")),[])\n' $O/e $GF $n > $O/e/t_$n.py; bash $O/tools/capvar.sh $n $O/e/t_$n.py $s > $O/rx/$n.res 2>$O/rx/$n.err; cat $O/rx/$n.res >> $O/results.jsonl; rm -rf $O/var/$n; }
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  run ${a[$i]} 0 & if [ $((i+1)) -lt ${#a[@]} ]; then run ${a[$((i+1))]} 1 & fi; wait; i=$((i+2))
done
