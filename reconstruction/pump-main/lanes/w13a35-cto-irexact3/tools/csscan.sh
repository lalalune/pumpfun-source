#!/bin/bash
# csscan.sh <base.ll> <listfile> <outjsonl>: lines "FN K ATTR"
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a35-cto-irexact3
while read -r fn k at; do n=cs_$(echo $fn|tr -dc 'a-z0-9')_${k}_$at
 r=$(CS_FN=$fn CS_K=$k CS_ATTR=$at python3 tools/rx.py $n tools/csedit.py --base $1 2>&1 | tail -1); echo "{\"item\":\"$fn $k $at\",\"r\":$r}" >> $3; rm -rf rx/$n; done < $2
