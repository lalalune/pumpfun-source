#!/bin/bash
# runq.sh <slot> <name>...: capvar e/<name>.py, append rx result to results.jsonl, then colour-map + event-piece force probe
O=~/.cache/pumpfun-reconstruction/lanes/w15a04-cto-n1event; W=$1; shift
for n in "$@"; do
  r=$(bash $O/tools/capvar.sh $n $O/e/$n.py $W 2>$O/rx_err_$n.txt | tail -1)
  rm -rf $O/var/$n; rm -f $O/ir/$n.ll
  [ -n "$r" ] || r="{\"name\":\"$n\",\"error\":\"none\"}"
  echo "$r" >> $O/results.jsonl
  if [ -f $O/rx/$n/m.ll ] && echo "$r" | grep -q ratio; then python3 $O/tools/probe.py $n >> $O/probe.jsonl 2>>$O/probe.err; fi
done
echo DONE$W
