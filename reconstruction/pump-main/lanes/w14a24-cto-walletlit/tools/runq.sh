#!/bin/bash
# runq.sh <slot> <names...>
cd ~/.cache/pumpfun-reconstruction/lanes/w14a24-cto-walletlit
s=$1; shift
for n in "$@"; do r=$(bash tools/capvar.sh $n e/$n.py $s 2>&1 | tail -1); echo "$r" >> ${RES:-res.jsonl}; rm -rf var/$n; done
