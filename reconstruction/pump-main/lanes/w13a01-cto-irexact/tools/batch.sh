#!/bin/bash
# batch.sh <list>: run capvar trials two at a time, append JSON to results_cap.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a01-cto-irexact; cd $OUT
run(){ while read -r n; do [ -z "$n" ] && continue; r=$(tools/capvar.sh $n e/$n.py $1 2>&1 | tail -1); echo "$r" >> results_cap.jsonl; rm -f ir/$n.ll; done; }
awk 'NR%2==1' $1 | run 0 &
awk 'NR%2==0' $1 | run 1 &
wait; echo "DONE $1" >> results_cap.jsonl
