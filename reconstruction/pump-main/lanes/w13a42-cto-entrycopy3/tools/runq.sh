#!/bin/bash
# runq.sh <slot> name... : sequential capvar runs on one work slot, results appended to res.jsonl
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a42-cto-entrycopy3; W=$1; shift
for n in "$@"; do r=$(bash $O/tools/capvar.sh $n $O/e/$n.py $W 2>&1 | tail -1); echo "$r" >> $O/res.jsonl; done
