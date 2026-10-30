#!/bin/bash
# runlist.sh <listfile> <workslot>: capvar each name sequentially, append result json to res_cap.jsonl
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a27-cto-seedsrpo; cd $OUT
for n in $(cat $1); do r=$(tools/capvar.sh $n e/$n.py $2 < /dev/null 2>&1 | tail -1); echo "$r" >> res_cap.jsonl; done
echo "{\"done\":\"$1\"}" >> res_cap.jsonl
