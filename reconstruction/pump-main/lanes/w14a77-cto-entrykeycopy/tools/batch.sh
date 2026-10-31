#!/bin/bash
# batch.sh name1 name2 ...: genes joined by '+'; 2 at a time
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a77-cto-entrykeycopy
run(){ n=$1; s=$2; printf 'import sys;sys.path.insert(0,"%s/e");import genes\nEDITS=sum((genes.G[g] for g in "%s".split("+")),[])\n' $O $n > $O/e/t_$n.py; bash $O/tools/capvar.sh $n $O/e/t_$n.py $s > $O/rx/$n.res 2>$O/rx/$n.err; if [ -f $O/rx/$n/m.o ]; then python3 $O/tools/entry.py $O/rx/$n/m.o | python3 -c "import json,sys;e=json.loads(sys.stdin.read());r=json.loads(open('$O/rx/$n.res').read() or '{}') if open('$O/rx/$n.res').read().strip().startswith('{') else {'name':'$n','error':open('$O/rx/$n.res').read()[:200]};r.update(e);print(json.dumps(r))" >> $O/results.jsonl; else echo "{\"name\":\"$n\",\"error\":\"compile\"}" >> $O/results.jsonl; fi; rm -rf $O/var/$n; }
a=("$@"); i=0
while [ $i -lt ${#a[@]} ]; do
  run ${a[$i]} 0 & if [ $((i+1)) -lt ${#a[@]} ]; then run ${a[$((i+1))]} 1 & fi; wait; i=$((i+2))
done
